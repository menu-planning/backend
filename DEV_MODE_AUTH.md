# Development Mode Authentication

This document explains how the development mode authentication system works, allowing you to develop without needing AWS Cognito while maintaining an identical authentication flow to production.

## Overview

In dev mode (`DEV_MODE_AUTH_BYPASS=true`), the application:
1. **Accepts any token** from the frontend in the Authorization header
2. **Ignores the token** and uses dev user claims from configuration
3. **Fetches the real dev user** from the database (user must exist!)
4. **Is completely transparent** to the frontend - no code changes needed!

## Key Principle

**The frontend doesn't know or care about dev mode.** It sends tokens exactly like in production, and the backend handles dev mode transparently.

## Architecture

### 1. Token Validation (`DevJWTValidator`)

Located in: `src/runtimes/fastapi/auth/jwt_validator.py`

**Dev Mode Behavior:**
- Accepts ANY token string from the Authorization header
- Ignores the token content completely
- Returns dev user claims from `app_config.py`
- User ID from claims matches the dev user in your database

**Key Method:**
```python
async def validate_token(self, token: str) -> CognitoJWTClaims:
    # Ignores token, returns dev user claims from config
    return CognitoJWTClaims(
        sub=config.dev_user_id,  # Must match user in DB!
        cognito_username=config.dev_user_email,
        cognito_groups=dev_roles,
        ...
    )
```

### 2. Database Lookup

Located in: `src/contexts/iam/core/internal_endpoints/get.py`

**Dev Mode Behavior:**
- Works exactly like production
- Queries database for user with `dev_user_id`
- Returns real user with real roles from database
- **⚠️ Dev user MUST exist in the database!**

## Configuration

### Environment Variables

```bash
# .env file
DEV_MODE_AUTH_BYPASS=true
DEV_USER_ID=a39cbaea-2031-7081-e1b8-76f4cabda1b3  # Must exist in DB!
DEV_USER_EMAIL=dev@localhost.dev
DEV_USER_ROLES=admin,user  # Optional, roles come from DB
```

### Configuration Object

Located in: `src/config/app_config.py`

```python
class APPSettings(BaseSettings):
    dev_mode_auth_bypass: bool = False  # Enable dev mode
    dev_user_id: str = "dev-user-123"   # Dev user ID (MUST exist in DB)
    dev_user_email: str = "dev@localhost.dev"
    dev_user_roles: str = "admin,user"  # Used in JWT claims
```

## Usage

### Frontend Integration

**No changes needed!** Your frontend works exactly the same:

```javascript
// Production code - works in dev mode too!
const response = await fetch('http://localhost:8000/clients/search', {
  headers: {
    'Authorization': `Bearer ${any_token_string}`  // Can be anything in dev mode
  }
});
```

### Quick Testing with cURL

```bash
# Any token works in dev mode (even "dummy")
curl -H "Authorization: Bearer dummy" http://localhost:8000/clients/search

# Or any random string
curl -H "Authorization: Bearer xyz123" http://localhost:8000/clients/search
```

### Testing with HTTPie

```bash
# Any token works
http GET http://localhost:8000/clients/search "Authorization: Bearer dummy"
```

## Flow Diagram

```
┌─────────────┐
│  Frontend   │ Same code as production!
└──────┬──────┘
       │ GET /clients/search
       │ Authorization: Bearer <any-token>
       ▼
┌────────────────────┐
│  JWTBearer         │
│  (security.py)     │
└────────┬───────────┘
         │ validate_token(<any-token>)
         ▼
┌────────────────────────────┐
│  DevJWTValidator           │
│  ✓ Ignores incoming token  │
│  ✓ Returns dev user claims │
│    from config             │
└────────┬───────────────────┘
         │ CognitoJWTClaims(sub=dev_user_id, ...)
         ▼
┌────────────────────┐
│  get_auth_context  │
│  (deps.py)         │
└────────┬───────────┘
         │ iam_provider.get_user(dev_user_id)
         ▼
┌────────────────────┐
│  IAM Internal API  │
│  (get.py)          │
│  ✓ Queries DB      │
│  ✓ Returns real    │
│    dev user        │
└────────┬───────────┘
         │ Real user object from DB
         ▼
┌─────────────┐
│  Endpoint   │ Processes request with real user
└─────────────┘
```

## Comparison: Dev Mode vs Production

| Aspect | Dev Mode | Production |
|--------|----------|------------|
| **Token Source** | Frontend sends any string | Frontend gets from Cognito |
| **Token Validation** | Ignored, uses config | Real Cognito validation |
| **User ID** | From `DEV_USER_ID` config | From JWT token |
| **User Lookup** | Real DB query | Real DB query |
| **User Object** | Real user from DB | Real user from DB |
| **Roles/Permissions** | Real roles from DB | Real roles from DB |
| **Frontend Changes** | **None!** | - |

## Prerequisites

### ⚠️ Critical: Dev User Must Exist in Database

The dev user specified by `DEV_USER_ID` **must exist** in your database with proper roles. 

**To verify:**
```sql
SELECT id, email FROM iam.users WHERE id = 'a39cbaea-2031-7081-e1b8-76f4cabda1b3';
```

**If the user doesn't exist, create it:**
```python
# Use your IAM user creation endpoint or script
# Ensure the user ID matches DEV_USER_ID in .env
```

## Benefits

1. **Zero Frontend Changes**: Frontend code works identically in dev and production
2. **Real Database**: Tests against actual database schema and constraints
3. **Real Roles**: Uses actual role-based access control from database
4. **Fast Development**: No network calls to Cognito
5. **Simple**: Just set `DEV_MODE_AUTH_BYPASS=true` and go!

## How It Works Internally

### When a request comes in:

1. **Frontend sends**: `Authorization: Bearer <any-string>`
2. **JWTBearer** extracts the token
3. **get_jwt_validator()** returns `DevJWTValidator` (because `DEV_MODE_AUTH_BYPASS=true`)
4. **DevJWTValidator.validate_token()**:
   - Ignores the incoming token completely
   - Creates claims with `dev_user_id` from config
   - Returns these claims
5. **get_auth_context()** uses the `dev_user_id` to fetch user from database
6. **IAM queries database** for user with that ID
7. **Real user object** with real roles is returned
8. **Request proceeds** with the real user context

## Security Notes

⚠️ **Dev mode should NEVER be enabled in production!**

- Any token is accepted (even "dummy")
- All requests are authenticated as the dev user
- No real security validation

The `DEV_MODE_AUTH_BYPASS` flag should only be `true` in local development environments.

## Troubleshooting

### "Recipes user not found" / "User not in database"

**Problem**: The dev user doesn't exist in the database.

**Solution**:
1. Check your `DEV_USER_ID` in `.env`
2. Verify this user exists in the database:
   ```sql
   SELECT * FROM iam.users WHERE id = 'your-dev-user-id';
   ```
3. If missing, create the user with proper roles
4. Ensure the user has roles for all contexts you need (recipes_catalog, products_catalog, etc.)

### Frontend still not working

**Check**:
1. `DEV_MODE_AUTH_BYPASS=true` in `.env`
2. Restart FastAPI server after changing `.env`
3. Frontend is sending Authorization header (even with dummy token)
4. Backend logs show "Using DevJWTValidator for authentication"

### Want to test with different users?

In dev mode, you're locked to one user. To test with different users:
1. Change `DEV_USER_ID` in `.env`
2. Restart the server
3. Ensure that user exists in DB

## Example: Complete Dev Setup

```bash
# 1. Set environment variables
cat >> .env << EOF
DEV_MODE_AUTH_BYPASS=true
DEV_USER_ID=a39cbaea-2031-7081-e1b8-76f4cabda1b3
DEV_USER_EMAIL=dev@localhost.dev
DEV_USER_ROLES=admin,user
EOF

# 2. Ensure dev user exists in database
# (Use your user creation script or endpoint)

# 3. Start server
uv run uvicorn src.runtimes.fastapi.main:app --reload

# 4. Test from frontend or curl
curl -H "Authorization: Bearer anything" http://localhost:8000/clients/search
```

That's it! No login endpoints, no token management, just pure development simplicity. 🚀

## When to Use Production Mode Locally

You might want to use real Cognito even in development when:
- Testing Cognito-specific features
- Testing with multiple real users
- Integration testing the full auth flow

To switch: Set `DEV_MODE_AUTH_BYPASS=false` and use real Cognito credentials.