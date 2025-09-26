"""Form response transfer service for updating existing clients with form data."""

import time
from typing import Any, Callable, Optional

from src.contexts.recipes_catalog.core.adapters.other_ctx_providers.client_onboarding.client_onboarding_provider import (
    ClientOnboardingProvider,
)
from src.contexts.recipes_catalog.core.domain.client.commands.update_client import (
    UpdateClient,
)
from src.contexts.recipes_catalog.core.services.client.command_handlers.update_client_handler import (
    update_client_handler,
)
from src.contexts.recipes_catalog.core.services.client.form_response_mapper import (
    FormResponseMapper,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.logging.logger import get_logger


class FormResponseTransferService:
    """
    Service for transferring form response data to existing clients.

    Provides methods to transfer TypeForm response data to existing clients
    through the update_client workflow, supporting both manual and automated
    transfer modes with preview capabilities.
    """

    def __init__(self):
        """Initialize the form response transfer service."""
        self.form_mapper = FormResponseMapper()
        self.logger = get_logger("FormResponseTransferService")

    async def transfer_form_response_to_client(
        self,
        client_id: str,
        form_response_id: str,
        uow_factory: Callable[[],UnitOfWork],
        preserve_existing: bool = True,
        custom_updates: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Transfer form response data to an existing client.

        Args:
            client_id: ID of the client to update
            form_response_id: TypeForm response ID to transfer
            uow: Unit of work for database operations
            preserve_existing: If True, only update fields that are None/empty
            custom_updates: Additional updates to apply alongside form data

        Returns:
            Dictionary with transfer results and warnings

        Raises:
            Exception: If client not found, form response not found, or transfer fails
        """
        start_time = time.perf_counter()

        self.logger.info(
            "Form response transfer started",
            operation_type="transfer_form_response_to_client",
            client_id=client_id,
            form_response_id=form_response_id,
            preserve_existing=preserve_existing,
            custom_updates_count=len(custom_updates) if custom_updates else 0
        )

        # Build update command with form response integration
        updates = {"form_response_id": form_response_id}

        # Add custom updates if provided
        if custom_updates:
            updates.update(custom_updates)

        # Create and execute update command
        update_cmd = UpdateClient(client_id=client_id, updates=updates)

        try:
            handler_start = time.perf_counter()
            await update_client_handler(update_cmd, uow_factory)
            handler_duration = time.perf_counter() - handler_start

            self.logger.debug(
                "Update client handler completed",
                operation_type="update_client_handler",
                client_id=client_id,
                duration_ms=round(handler_duration * 1000, 2)
            )

            # Get transfer results for return value
            async with uow_factory() as uow:
                updated_client = await uow.clients.get(client_id)

                result = {
                    "status": "success",
                    "client_id": client_id,
                    "form_response_id": form_response_id,
                    "transfer_summary": {
                        "profile_updated": bool(updated_client.profile),
                        "contact_info_updated": bool(updated_client.contact_info),
                        "address_updated": bool(updated_client.address),
                        "onboarding_data_stored": bool(updated_client.onboarding_data),
                        "notes_enhanced": bool(updated_client.notes)
                    },
                    "preserve_existing": preserve_existing,
                    "custom_updates_applied": list(custom_updates.keys()) if custom_updates else []
                }

                total_duration = time.perf_counter() - start_time
                self.logger.info(
                    "Form response transfer completed",
                    operation_type="transfer_form_response_to_client",
                    client_id=client_id,
                    form_response_id=form_response_id,
                    duration_ms=round(total_duration * 1000, 2),
                    status="success",
                    fields_updated=sum(result["transfer_summary"].values())
                )

                return result

        except Exception as e:
            total_duration = time.perf_counter() - start_time
            self.logger.error(
                "Form response transfer failed",
                operation_type="transfer_form_response_to_client",
                client_id=client_id,
                form_response_id=form_response_id,
                duration_ms=round(total_duration * 1000, 2),
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )

            return {
                "status": "error",
                "client_id": client_id,
                "form_response_id": form_response_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def preview_form_response_transfer(
        self,
        client_id: str,
        form_response_id: str,
        uow_factory: Callable[[],UnitOfWork]
    ) -> dict[str, Any]:
        """
        Preview what would happen if form response data is transferred to a client.

        Args:
            client_id: ID of the client to preview update for
            form_response_id: TypeForm response ID to preview
            uow: Unit of work for database operations

        Returns:
            Dictionary with preview data showing before/after comparison

        Raises:
            Exception: If client not found or form response not found
        """
        try:
            # Get current client data
            async with uow_factory() as uow:
                current_client = await uow.clients.get(client_id)

            # Get form response data
            form_response_data = await ClientOnboardingProvider.get_form_response(form_response_id)

            # Map form response to client data
            client_params, extraction_warnings = self.form_mapper.map_form_response_to_client_data(
                form_response=form_response_data,
                author_id=current_client.author_id
            )

            # Build preview comparison
            preview = {
                "client_id": client_id,
                "form_response_id": form_response_id,
                "status": "preview",
                "current_data": {
                    "profile": {
                        "name": current_client.profile.name if current_client.profile else None,
                        "sex": current_client.profile.sex if current_client.profile else None,
                        "birthday": current_client.profile.birthday.isoformat() if current_client.profile and current_client.profile.birthday else None,
                    },
                    "contact_info": {
                        "email": current_client.contact_info.main_email if current_client.contact_info else None,
                        "phone": current_client.contact_info.main_phone if current_client.contact_info else None,
                        "all_emails": list(current_client.contact_info.all_emails) if current_client.contact_info else [],
                        "all_phones": list(current_client.contact_info.all_phones) if current_client.contact_info else [],
                    } if current_client.contact_info else None,
                    "address": {
                        "street": current_client.address.street if current_client.address else None,
                        "city": current_client.address.city if current_client.address else None,
                        "state": current_client.address.state if current_client.address else None,
                        "complement": current_client.address.complement if current_client.address else None,
                        "zip_code": current_client.address.zip_code if current_client.address else None,
                    } if current_client.address else None,
                    "notes": current_client.notes,
                    "has_onboarding_data": bool(current_client.onboarding_data)
                },
                "proposed_data": {
                    "profile": {
                        "name": client_params["profile"].name if client_params.get("profile") else None,
                        "sex": client_params["profile"].sex if client_params.get("profile") else None,
                        "birthday": client_params["profile"].birthday.isoformat() if client_params.get("profile") and client_params["profile"].birthday else None,
                    } if client_params.get("profile") else None,
                    "contact_info": {
                        "email": client_params["contact_info"].main_email if client_params.get("contact_info") else None,
                        "phone": client_params["contact_info"].main_phone if client_params.get("contact_info") else None,
                        "all_emails": list(client_params["contact_info"].all_emails) if client_params.get("contact_info") else [],
                        "all_phones": list(client_params["contact_info"].all_phones) if client_params.get("contact_info") else [],
                    } if client_params.get("contact_info") else None,
                    "address": {
                        "street": client_params["address"].street if client_params.get("address") else None,
                        "city": client_params["address"].city if client_params.get("address") else None,
                        "state": client_params["address"].state if client_params.get("address") else None,
                        "complement": client_params["address"].complement if client_params.get("address") else None,
                        "zip_code": client_params["address"].zip_code if client_params.get("address") else None,
                    } if client_params.get("address") else None,
                    "notes": client_params.get("notes"),
                    "onboarding_data_will_be_stored": bool(form_response_data)
                },
                "extraction_warnings": extraction_warnings,
                "changes_summary": self._analyze_changes(current_client, client_params)
            }

            return preview

        except Exception as e:
            return {
                "status": "error",
                "client_id": client_id,
                "form_response_id": form_response_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def batch_transfer_form_responses(
        self,
        transfers: list[dict[str, Any]],
        uow_factory: Callable[[],UnitOfWork]
    ) -> dict[str, Any]:
        """
        Transfer multiple form responses to multiple clients in batch.

        Args:
            transfers: List of transfer specifications, each containing:
                - client_id: ID of client to update
                - form_response_id: TypeForm response ID
                - preserve_existing: Whether to preserve existing data (optional)
                - custom_updates: Additional updates (optional)
            uow: Unit of work for database operations

        Returns:
            Dictionary with batch operation results
        """
        results = {
            "total_transfers": len(transfers),
            "successful_transfers": 0,
            "failed_transfers": 0,
            "results": [],
            "status": "completed"
        }

        for transfer_spec in transfers:
            try:
                client_id = transfer_spec["client_id"]
                form_response_id = transfer_spec["form_response_id"]
                preserve_existing = transfer_spec.get("preserve_existing", True)
                custom_updates = transfer_spec.get("custom_updates")

                transfer_result = await self.transfer_form_response_to_client(
                    client_id=client_id,
                    form_response_id=form_response_id,
                    uow_factory=uow_factory,
                    preserve_existing=preserve_existing,
                    custom_updates=custom_updates
                )

                if transfer_result["status"] == "success":
                    results["successful_transfers"] += 1
                else:
                    results["failed_transfers"] += 1

                results["results"].append(transfer_result)

            except Exception as e:
                results["failed_transfers"] += 1
                results["results"].append({
                    "status": "error",
                    "client_id": transfer_spec.get("client_id", "unknown"),
                    "form_response_id": transfer_spec.get("form_response_id", "unknown"),
                    "error": str(e),
                    "error_type": type(e).__name__
                })

        return results

    def _analyze_changes(self, current_client, proposed_params: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze what changes would be made during transfer.

        Args:
            current_client: Current client entity
            proposed_params: Proposed update parameters from form mapping

        Returns:
            Dictionary describing the changes that would be made
        """
        changes = {
            "profile_changes": [],
            "contact_info_changes": [],
            "address_changes": [],
            "notes_changes": False,
            "onboarding_data_changes": False,
            "total_field_updates": 0
        }

        # Analyze profile changes
        if proposed_params.get("profile"):
            if not current_client.profile:
                changes["profile_changes"].append("Profile will be created")
                changes["total_field_updates"] += 1
            else:
                proposed_profile = proposed_params["profile"]
                if current_client.profile.name != proposed_profile.name:
                    changes["profile_changes"].append(f"Name: '{current_client.profile.name}' → '{proposed_profile.name}'")
                    changes["total_field_updates"] += 1
                if current_client.profile.age != proposed_profile.age:
                    changes["profile_changes"].append(f"Age: {current_client.profile.age} → {proposed_profile.age}")
                    changes["total_field_updates"] += 1

        # Analyze contact info changes
        if proposed_params.get("contact_info"):
            if not current_client.contact_info:
                changes["contact_info_changes"].append("Contact info will be created")
                changes["total_field_updates"] += 1
            else:
                proposed_contact = proposed_params["contact_info"]
                if current_client.contact_info.email != proposed_contact.email:
                    changes["contact_info_changes"].append(f"Email: '{current_client.contact_info.email}' → '{proposed_contact.email}'")
                    changes["total_field_updates"] += 1

        # Analyze address changes
        if proposed_params.get("address"):
            if not current_client.address:
                changes["address_changes"].append("Address will be created")
                changes["total_field_updates"] += 1
            else:
                proposed_address = proposed_params["address"]
                if current_client.address.city != proposed_address.city:
                    changes["address_changes"].append(f"City: '{current_client.address.city}' → '{proposed_address.city}'")
                    changes["total_field_updates"] += 1

        # Analyze notes and onboarding data
        if proposed_params.get("notes") and proposed_params["notes"] != current_client.notes:
            changes["notes_changes"] = True
            changes["total_field_updates"] += 1

        if proposed_params.get("onboarding_data") and proposed_params["onboarding_data"] != current_client.onboarding_data:
            changes["onboarding_data_changes"] = True
            changes["total_field_updates"] += 1

        return changes
