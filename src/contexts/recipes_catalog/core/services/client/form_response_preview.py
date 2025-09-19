"""Form response preview service for client data transfer workflows."""

import time
from datetime import datetime
from typing import Any

from src.contexts.recipes_catalog.core.adapters.other_ctx_providers.client_onboarding.client_onboarding_provider import (
    ClientOnboardingProvider,
)
from src.contexts.recipes_catalog.core.services.client.form_response_mapper import (
    FormResponseMapper,
)
from src.logging.logger import get_logger


class FormResponsePreviewService:
    """Preview what client data would look like before transfer."""

    def __init__(self):
        """Initialize the form response preview service."""
        self.form_mapper = FormResponseMapper()
        self.onboarding_provider = ClientOnboardingProvider()
        self.logger = get_logger("FormResponsePreviewService")

    async def preview_form_response_for_client_creation(
        self,
        response_id: str,
        author_id: str
    ) -> dict[str, Any]:
        """
        Preview what client data would look like for a specific form response.

        Args:
            response_id: The TypeForm response ID
            author_id: The ID of the user who would create the client

        Returns:
            Dictionary with preview data and metadata

        Raises:
            ValueError: If response not found or invalid parameters
        """
        start_time = time.perf_counter()

        self.logger.info(
            "Form response preview started",
            operation_type="preview_form_response",
            response_id=response_id,
            author_id=author_id
        )

        if not response_id:
            raise ValueError("Response ID is required")
        if not author_id:
            raise ValueError("Author ID is required")

        try:
            # Get form response data from client_onboarding context
            provider_start = time.perf_counter()
            try:
                form_response_data = await self.onboarding_provider.get_form_response(response_id)
            except Exception as e:
                raise ValueError(f"Failed to retrieve form response {response_id}: {e!s}") from e
            finally:
                provider_duration = time.perf_counter() - provider_start
                self.logger.debug(
                    "External provider call completed",
                    operation_type="get_form_response",
                    response_id=response_id,
                    duration_ms=round(provider_duration * 1000, 2),
                    provider="client_onboarding"
                )

            if not form_response_data or not form_response_data.get("success"):
                raise ValueError(f"Form response {response_id} not found or inaccessible")

            response_data = form_response_data.get("response")
            if not response_data:
                raise ValueError(f"No response data found for {response_id}")

            # Generate preview using form response mapper
            mapper_start = time.perf_counter()
            preview_result = self.form_mapper.preview_client_data_from_form_response(response_data, author_id)
            mapper_duration = time.perf_counter() - mapper_start

            self.logger.debug(
                "Form response mapping completed",
                operation_type="preview_client_data_mapping",
                response_id=response_id,
                duration_ms=round(mapper_duration * 1000, 2),
                fields_mapped=len(preview_result.get("client_data", {}))
            )

            # Add metadata and frontend-friendly information
            enhanced_preview = {
                **preview_result,
                "metadata": {
                    "response_id": response_id,
                    "author_id": author_id,
                    "preview_generated_at": datetime.now().isoformat(),
                    "form_title": response_data.get("definition", {}).get("title", "Unknown Form"),
                    "submitted_at": response_data.get("submitted_at"),
                    "response_status": response_data.get("status", "unknown")
                },
                "client_creation_readiness": {
                    "can_create_client": preview_result.get("required_fields_present", False),
                    "missing_required_fields": self._identify_missing_required_fields(preview_result),
                    "data_quality_score": self._calculate_data_quality_score(preview_result),
                    "recommendations": self._generate_recommendations(preview_result)
                }
            }

            total_duration = time.perf_counter() - start_time
            self.logger.info(
                "Form response preview completed",
                operation_type="preview_form_response",
                response_id=response_id,
                author_id=author_id,
                duration_ms=round(total_duration * 1000, 2),
                can_create_client=enhanced_preview["client_creation_readiness"]["can_create_client"],
                data_quality_score=enhanced_preview["client_creation_readiness"]["data_quality_score"]
            )

            return enhanced_preview

        except Exception as e:
            total_duration = time.perf_counter() - start_time
            self.logger.error(
                "Form response preview failed",
                operation_type="preview_form_response",
                response_id=response_id,
                author_id=author_id,
                duration_ms=round(total_duration * 1000, 2),
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            raise

    async def preview_multiple_form_responses(
        self,
        response_ids: list[str],
        author_id: str
    ) -> dict[str, Any]:
        """
        Preview multiple form responses for batch client creation assessment.

        Args:
            response_ids: List of TypeForm response IDs
            author_id: The ID of the user who would create the clients

        Returns:
            Dictionary with previews for all responses and batch summary

        Raises:
            ValueError: If invalid parameters
        """
        start_time = time.perf_counter()

        self.logger.info(
            "Batch form response preview started",
            operation_type="preview_multiple_form_responses",
            author_id=author_id,
            response_count=len(response_ids) if response_ids else 0
        )

        if not response_ids:
            raise ValueError("At least one response ID is required")
        if len(response_ids) > 10:
            raise ValueError("Maximum 10 responses can be previewed at once")
        if not author_id:
            raise ValueError("Author ID is required")

        previews = {}
        batch_summary = {
            "total_responses": len(response_ids),
            "ready_for_creation": 0,
            "partial_data": 0,
            "failed_previews": 0,
            "average_quality_score": 0.0,
            "common_missing_fields": {},
            "batch_recommendations": []
        }

        quality_scores = []
        all_missing_fields = []

        for response_id in response_ids:
            try:
                preview = await self.preview_form_response_for_client_creation(response_id, author_id)
                previews[response_id] = preview

                # Update batch summary
                if preview.get("client_creation_readiness", {}).get("can_create_client", False):
                    batch_summary["ready_for_creation"] += 1
                elif preview.get("extraction_success", False):
                    batch_summary["partial_data"] += 1

                quality_score = preview.get("client_creation_readiness", {}).get("data_quality_score", 0)
                quality_scores.append(quality_score)

                missing_fields = preview.get("client_creation_readiness", {}).get("missing_required_fields", [])
                all_missing_fields.extend(missing_fields)

            except Exception as e:
                previews[response_id] = {
                    "error": str(e),
                    "extraction_success": False,
                    "required_fields_present": False
                }
                batch_summary["failed_previews"] += 1

        # Calculate batch statistics
        if quality_scores:
            batch_summary["average_quality_score"] = sum(quality_scores) / len(quality_scores)

        # Count common missing fields
        if all_missing_fields:
            field_counts = {}
            for field in all_missing_fields:
                field_counts[field] = field_counts.get(field, 0) + 1
            batch_summary["common_missing_fields"] = field_counts

        # Generate batch recommendations
        batch_summary["batch_recommendations"] = self._generate_batch_recommendations(batch_summary)

        total_duration = time.perf_counter() - start_time
        self.logger.info(
            "Batch form response preview completed",
            operation_type="preview_multiple_form_responses",
            author_id=author_id,
            response_count=len(response_ids),
            duration_ms=round(total_duration * 1000, 2),
            ready_for_creation=batch_summary["ready_for_creation"],
            failed_previews=batch_summary["failed_previews"],
            average_quality_score=batch_summary["average_quality_score"]
        )

        return {
            "previews": previews,
            "batch_summary": batch_summary,
            "generated_at": datetime.now().isoformat()
        }

    async def get_form_responses_for_client_selection(
        self,
        author_id: str,
        form_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
        include_preview: bool = False
    ) -> dict[str, Any]:
        """
        Get form responses suitable for client creation with optional previews.

        Args:
            author_id: The ID of the user requesting the responses
            form_id: Optional form ID to filter responses
            limit: Maximum number of responses to return
            offset: Offset for pagination
            include_preview: Whether to include client data previews

        Returns:
            Dictionary with form responses and metadata
        """
        start_time = time.perf_counter()

        self.logger.info(
            "Form responses selection started",
            operation_type="get_form_responses_for_client_selection",
            author_id=author_id,
            form_id=form_id,
            limit=limit,
            offset=offset,
            include_preview=include_preview
        )

        try:
            # Get form responses from client_onboarding context
            provider_start = time.perf_counter()
            form_id_int = int(form_id) if form_id else None
            responses = await self.onboarding_provider.get_form_responses(
                form_id=form_id_int,
                limit=limit,
                offset=offset
            )
            provider_duration = time.perf_counter() - provider_start

            self.logger.debug(
                "Form responses retrieved from provider",
                operation_type="get_form_responses",
                author_id=author_id,
                form_id=form_id,
                duration_ms=round(provider_duration * 1000, 2),
                response_count=len(responses) if responses else 0
            )

            if not responses:
                return {
                    "success": False,
                    "responses": [],
                    "total": 0,
                    "error": "No form responses found"
                }

            # Enhance responses with client creation readiness info
            enhanced_responses = []
            for response in responses:
                enhanced_response = {
                    **response,
                    "client_creation_readiness": {
                        "assessed": False,
                        "can_create_client": None,
                        "quality_score": None
                    }
                }

                # Add preview if requested
                if include_preview:
                    try:
                        response_id = response.get("response_id")
                        if response_id:
                            preview = await self.preview_form_response_for_client_creation(response_id, author_id)
                            enhanced_response["client_creation_readiness"] = {
                                "assessed": True,
                                "can_create_client": preview.get("required_fields_present", False),
                                "quality_score": preview.get("client_creation_readiness", {}).get("data_quality_score", 0),
                                "preview_data": preview.get("preview"),
                                "warnings": preview.get("warnings", {})
                            }
                    except Exception:
                        # Skip preview on error, keep basic response data
                        pass

                enhanced_responses.append(enhanced_response)

            total_duration = time.perf_counter() - start_time
            self.logger.info(
                "Form responses selection completed",
                operation_type="get_form_responses_for_client_selection",
                author_id=author_id,
                form_id=form_id,
                duration_ms=round(total_duration * 1000, 2),
                response_count=len(enhanced_responses),
                include_preview=include_preview
            )

            return {
                "success": True,
                "responses": enhanced_responses,
                "total": len(enhanced_responses),
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": len(enhanced_responses) == limit
                },
                "metadata": {
                    "author_id": author_id,
                    "form_id": form_id,
                    "include_preview": include_preview,
                    "retrieved_at": datetime.now().isoformat()
                }
            }

        except Exception as e:
            total_duration = time.perf_counter() - start_time
            self.logger.error(
                "Form responses selection failed",
                operation_type="get_form_responses_for_client_selection",
                author_id=author_id,
                form_id=form_id,
                duration_ms=round(total_duration * 1000, 2),
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )

            return {
                "success": False,
                "responses": [],
                "total": 0,
                "error": f"Failed to retrieve form responses: {e!s}"
            }

    def _identify_missing_required_fields(self, preview_result: dict[str, Any]) -> list[str]:
        """Identify which required fields are missing from the preview."""
        missing_fields = []

        preview_data = preview_result.get("preview", {})
        if not preview_data:
            return ["all_fields"]

        # Check required profile fields
        profile = preview_data.get("profile", {})
        if not profile or not profile.get("name"):
            missing_fields.append("profile.name")

        return missing_fields

    def _calculate_data_quality_score(self, preview_result: dict[str, Any]) -> float:
        """Calculate a data quality score (0-100) based on available fields."""
        if not preview_result.get("extraction_success", False):
            return 0.0

        preview_data = preview_result.get("preview", {})
        if not preview_data:
            return 0.0

        score = 0.0
        max_score = 100.0

        # Profile scoring (60% of total score)
        profile = preview_data.get("profile", {})
        if profile:
            if profile.get("name"):
                score += 40.0  # Name is critical
            if profile.get("age"):
                score += 10.0
            if profile.get("dietary_preferences"):
                score += 10.0

        # Contact info scoring (25% of total score)
        contact_info = preview_data.get("contact_info")
        if contact_info:
            if contact_info.get("email"):
                score += 15.0
            if contact_info.get("phone"):
                score += 10.0

        # Address scoring (15% of total score)
        address = preview_data.get("address")
        if address and address.get("street") and address.get("city"):
            score += 15.0

        return min(score, max_score)

    def _generate_recommendations(self, preview_result: dict[str, Any]) -> list[str]:
        """Generate recommendations for improving client data quality."""
        recommendations = []

        if not preview_result.get("extraction_success", False):
            recommendations.append("Review form response data for extraction errors")
            return recommendations

        preview_data = preview_result.get("preview", {})
        warnings = preview_result.get("warnings", {})

        # Profile recommendations
        profile = preview_data.get("profile", {})
        if not profile or not profile.get("name"):
            recommendations.append("Client name is required - check form response for name fields")
        if profile and not profile.get("age"):
            recommendations.append("Consider adding age information for better client profiling")

        # Contact recommendations
        if not preview_data.get("contact_info"):
            recommendations.append("Add contact information (email or phone) for client communication")

        # Address recommendations
        if not preview_data.get("address"):
            recommendations.append("Consider adding address information for delivery and location services")

        # Warning-based recommendations
        if warnings:
            recommendations.append("Review extraction warnings and consider manual data entry for missing fields")

        return recommendations

    def _generate_batch_recommendations(self, batch_summary: dict[str, Any]) -> list[str]:
        """Generate recommendations for batch processing."""
        recommendations = []

        total = batch_summary["total_responses"]
        ready = batch_summary["ready_for_creation"]
        partial = batch_summary["partial_data"]
        failed = batch_summary["failed_previews"]

        if ready == total:
            recommendations.append("All responses are ready for automatic client creation")
        elif ready > 0:
            recommendations.append(f"{ready} responses ready for creation, {partial + failed} need review")
        else:
            recommendations.append("No responses ready for automatic creation - manual review required")

        # Common field recommendations
        common_missing = batch_summary.get("common_missing_fields", {})
        if common_missing:
            most_common = max(common_missing.items(), key=lambda x: x[1])
            recommendations.append(f"Most common missing field: {most_common[0]} (missing in {most_common[1]} responses)")

        avg_quality = batch_summary.get("average_quality_score", 0)
        if avg_quality < 50:
            recommendations.append("Consider improving form design to capture more complete client data")

        return recommendations
