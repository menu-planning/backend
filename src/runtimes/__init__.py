"""Runtime-specific infrastructure for different deployment targets.

This package provides runtime-specific implementations for:
- FastAPI: Web framework for local development and containerized deployments
- AWS Lambda: Serverless functions for cloud deployment

Each runtime maintains its own middleware, dependency injection, and
endpoint patterns while sharing the same business logic from contexts.
"""
