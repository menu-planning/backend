#!/usr/bin/env python3
"""
Local Lambda Server for Testing

Wraps AWS Lambda handlers in a simple HTTP server for local testing with ngrok.
This allows testing Lambda functions locally without deploying to AWS.
Uses built-in http.server to avoid external dependencies.
"""

import json
import os
import sys
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import your Lambda handlers
webhook_lambda_handler = None
create_form_lambda_handler = None

try:
    from contexts.client_onboarding.aws_lambda.webhook_processor import async_lambda_handler as webhook_lambda_handler # type: ignore
    from contexts.client_onboarding.aws_lambda.create_form import async_handler as create_form_lambda_handler # type: ignore
    print("✓ Successfully imported Lambda handlers")
except ImportError as e:
    print(f"⚠ Warning: Could not import Lambda handlers: {e}")
    print("  Make sure you're running from the correct directory and dependencies are installed")


def create_lambda_event(method: str, path: str, headers: Dict[str, str], body: Optional[str], query_params: Dict[str, str]) -> Dict[str, Any]:
    """Convert HTTP request to AWS Lambda event format."""
    return {
        "httpMethod": method,
        "path": path,
        "queryStringParameters": query_params or None,
        "headers": headers,
        "body": body,
        "isBase64Encoded": False,
        "requestContext": {
            "requestId": "local-test-request",
            "stage": "test",
            "httpMethod": method,
            "path": path,
        }
    }


def create_lambda_context():
    """Create mock Lambda context for local testing."""
    class MockContext:
        def __init__(self):
            self.function_name = "local-test-function"
            self.function_version = "$LATEST"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:local-test"
            self.memory_limit_in_mb = "128"
            self.remaining_time_in_millis = lambda: 30000
            self.aws_request_id = "local-test-request-id"
    
    return MockContext()


class LambdaHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler that wraps Lambda functions."""
    
    def log_message(self, format, *args):
        """Override to control logging output."""
        print(f"{self.address_string()} - {format % args}")
    
    def _set_response(self, status_code: int = 200, headers: Optional[Dict[str, str]] = None):
        """Set HTTP response headers."""
        self.send_response(status_code)
        
        # Always add CORS headers for testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Typeform-Signature')
        
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        
        self.send_header('Content-type', 'application/json')
        self.end_headers()
    
    def _get_request_body(self) -> Optional[str]:
        """Read and return request body."""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            return self.rfile.read(content_length).decode('utf-8')
        return None
    
    def _handle_lambda_request(self, handler, handler_name: str):
        """Generic handler for Lambda requests."""
        if not handler:
            self._set_response(500)
            response = {"error": f"{handler_name} handler not available"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
        
        try:
            # Parse request
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Flatten query params (parse_qs returns lists)
            flattened_params = {k: v[0] if v else '' for k, v in query_params.items()}
            
            # Get request body
            body = self._get_request_body()
            
            # Create Lambda event and context
            event = create_lambda_event(
                method=self.command,
                path=parsed_url.path,
                headers=dict(self.headers),
                body=body,
                query_params=flattened_params
            )
            context = create_lambda_context()
            
            # Call the async Lambda handler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                lambda_response = loop.run_until_complete(handler(event, context))
            finally:
                loop.close()
            
            # Send response
            status_code = lambda_response.get("statusCode", 200)
            response_headers = lambda_response.get("headers", {})
            response_body = lambda_response.get("body", "{}")
            
            self._set_response(status_code, response_headers)
            self.wfile.write(response_body.encode('utf-8'))
            
        except Exception as e:
            print(f"Error processing {handler_name}: {e}")
            import traceback
            traceback.print_exc()
            
            self._set_response(500)
            error_response = {
                "error": f"{handler_name} processing failed",
                "details": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self._set_response(200)
        self.wfile.write(b'')
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path.startswith('/webhook'):
            self._handle_lambda_request(webhook_lambda_handler, "Webhook")
        elif self.path.startswith('/onboarding-forms'):
            self._handle_lambda_request(create_form_lambda_handler, "Create Form")
        else:
            self._set_response(404)
            response = {"error": "Endpoint not found", "available_endpoints": ["/webhook", "/onboarding-forms"]}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self._set_response(200)
            response = {"status": "healthy", "service": "local-lambda-server"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif self.path.startswith('/webhook'):
            # Handle webhook validation/ping requests
            self._set_response(200)
            response = {
                "status": "webhook_endpoint_ready",
                "message": "Webhook endpoint is accessible",
                "service": "local-lambda-server"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif self.path == '/':
            self._set_response(200)
            response = {
                "service": "Local Lambda Server",
                "endpoints": {
                    "webhook": "POST /webhook (with GET validation)",
                    "create_form": "POST /onboarding-forms",
                    "health": "GET /health"
                }
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self._set_response(404)
            response = {"error": "Endpoint not found"}
            self.wfile.write(json.dumps(response).encode('utf-8'))


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the local Lambda server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, LambdaHTTPHandler)
    
    print(f"🚀 Local Lambda Server running on http://{host}:{port}")
    print()
    print("Available endpoints:")
    print("  POST /webhook - Webhook processor")
    print("  GET /webhook - Webhook validation/ping")
    print("  POST /onboarding-forms - Create onboarding form")
    print("  GET /health - Health check")
    print("  GET / - Service info")
    print()
    print("To expose with ngrok: ngrok http 8000")
    print()
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()


if __name__ == "__main__":
    # Load environment variables for local testing
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    run_server(host, port)