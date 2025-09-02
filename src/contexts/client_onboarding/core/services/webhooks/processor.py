"""Webhook payload processor for TypeForm form responses.

Process and validate incoming TypeForm webhook payloads, extract client
identifiers, and store form response data with comprehensive error handling.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.contexts.client_onboarding.core.domain.models.form_response import FormResponse
from src.contexts.client_onboarding.core.services.exceptions import (
    DatabaseOperationError,
    FormResponseProcessingError,
    OnboardingFormNotFoundError,
    WebhookPayloadError,
)
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.logging.logger import StructlogFactory

logger = StructlogFactory.get_logger(__name__)


@dataclass
class FormFieldResponse:
    """Represents a single field response from a TypeForm submission.

    Attributes:
        field_id: Unique identifier for the form field.
        field_type: Type of the form field (e.g., 'email', 'short_text').
        question: The question text displayed to the user.
        answer: The user's response value.
        field_ref: Optional reference identifier for the field.
    """
    field_id: str
    field_type: str
    question: str
    answer: Any
    field_ref: str | None = None


@dataclass
class ProcessedWebhookData:
    """Processed webhook data containing extracted form response information.

    Attributes:
        event_id: Unique identifier for the webhook event.
        event_type: Type of the webhook event.
        form_id: TypeForm form identifier.
        response_token: Unique token for the form response.
        submitted_at: Timestamp when the form was submitted.
        field_responses: List of processed field responses.
        metadata: Additional webhook metadata.
        client_identifiers: Extracted client identification data.
    """
    event_id: str
    event_type: str
    form_id: str
    response_token: str
    submitted_at: datetime
    field_responses: list[FormFieldResponse]
    metadata: dict[str, Any]
    client_identifiers: dict[str, str]


class WebhookPayloadProcessor:
    """Processes TypeForm webhook payloads and extracts client data.

    Handles the complete lifecycle of webhook payload processing including
    validation, data extraction, client identifier detection, and storage.
    """

    def __init__(self, uow: UnitOfWork):
        """Initialize the webhook payload processor.

        Args:
            uow: Unit of work for database operations.
        """
        self.uow = uow

    async def process_webhook_payload(self, payload_dict: dict[str, Any]) -> ProcessedWebhookData:
        """Process a TypeForm webhook payload and extract structured data.

        Args:
            payload_dict: Raw webhook payload from TypeForm.

        Returns:
            Processed webhook data with extracted client identifiers.

        Raises:
            WebhookPayloadError: For invalid payload structure or data.
            FormResponseProcessingError: For processing failures.
            OnboardingFormNotFoundError: If the form is not found.
        """
        try:
            logger.info(
                "Processing webhook payload",
                event_id=payload_dict.get('event_id', 'unknown'),
                action="webhook_payload_process",
                form_id=payload_dict.get('form_response', {}).get('form_id'),
                event_type=payload_dict.get('event_type'),
                webhook_source="typeform",
                processing_stage="payload_extraction",
                business_context="form_response_processing"
            )
            event_info = await self._extract_event_info(payload_dict)
            await self._verify_form_exists(event_info['form_id'])
            field_responses = await self._process_form_responses(payload_dict.get('form_response', {}))
            client_identifiers = await self._extract_client_identifiers(field_responses)
            metadata = await self._extract_metadata(payload_dict)
            return ProcessedWebhookData(
                event_id=event_info['event_id'],
                event_type=event_info['event_type'],
                form_id=event_info['form_id'],
                response_token=event_info['response_token'],
                submitted_at=event_info['submitted_at'],
                field_responses=field_responses,
                metadata=metadata,
                client_identifiers=client_identifiers,
            )
        except (WebhookPayloadError, FormResponseProcessingError, OnboardingFormNotFoundError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error processing webhook payload: {e!s}"
            logger.error(
                "Unexpected error processing webhook payload",
                error=str(e),
                action="webhook_payload_unexpected_error",
                event_id=payload_dict.get('event_id', 'unknown'),
                form_id=payload_dict.get('form_response', {}).get('form_id'),
                event_type=payload_dict.get('event_type'),
                webhook_source="typeform",
                processing_stage="unexpected_error",
                business_impact="webhook_processing_failed",
                exc_info=True
            )
            raise FormResponseProcessingError("unknown", "payload_processing", error_msg) from e

    async def _extract_event_info(self, payload_dict: dict[str, Any]) -> dict[str, Any]:
        """Extract event information from webhook payload.

        Args:
            payload_dict: Raw webhook payload.

        Returns:
            Dictionary containing event metadata.

        Raises:
            WebhookPayloadError: For missing or invalid event data.
        """
        try:
            form_response = payload_dict.get('form_response', {})
            submitted_at_str = form_response.get('submitted_at')
            if not submitted_at_str:
                raise WebhookPayloadError("Missing submitted_at timestamp")
            try:
                submitted_at = datetime.fromisoformat(submitted_at_str.replace('Z', '+00:00'))
                submitted_at = submitted_at.astimezone(UTC).replace(tzinfo=None)
            except ValueError as e:
                raise WebhookPayloadError(f"Invalid submitted_at format: {submitted_at_str}") from e
            return {
                'event_id': payload_dict.get('event_id'),
                'event_type': payload_dict.get('event_type'),
                'form_id': form_response.get('form_id'),
                'response_token': form_response.get('token'),
                'submitted_at': submitted_at,
            }
        except Exception as e:
            if isinstance(e, WebhookPayloadError):
                raise
            raise WebhookPayloadError(f"Error extracting event info: {e!s}") from e

    async def _verify_form_exists(self, form_id: str) -> None:
        """Verify that the form exists in the database.

        Args:
            form_id: TypeForm form identifier.

        Raises:
            OnboardingFormNotFoundError: If the form is not found.
            DatabaseOperationError: For database access errors.
        """
        try:
            form = await self.uow.onboarding_forms.get_by_typeform_id(form_id)
            if not form:
                raise OnboardingFormNotFoundError(f"Form not found: {form_id}")
            logger.info("Form verification successful", form_id=form_id, db_id=form.id, action="form_verification", business_context="webhook_processing")
        except Exception as e:
            if isinstance(e, OnboardingFormNotFoundError):
                raise
            raise DatabaseOperationError("form_verification", "onboarding_form", str(e)) from e

    async def _process_form_responses(self, form_response: dict[str, Any]) -> list[FormFieldResponse]:
        """Process form response answers into structured field responses.

        Args:
            form_response: Form response data from webhook payload.

        Returns:
            List of processed field responses.

        Raises:
            WebhookPayloadError: For invalid form response structure.
        """
        try:
            answers = form_response.get('answers', [])
            if not isinstance(answers, list):
                raise WebhookPayloadError("Form answers must be a list")
            field_responses: list[FormFieldResponse] = []
            for answer in answers:
                if not isinstance(answer, dict):
                    logger.warning("Skipping malformed answer", answer=answer, action="answer_validation_skip")
                    continue
                try:
                    field_response = await self._parse_field_answer(answer)
                    if field_response:
                        field_responses.append(field_response)
                except Exception as e:
                    logger.warning("Error parsing field answer", error=str(e), answer=answer, action="field_parse_error")
                    continue
            logger.info("Field responses processed", response_count=len(field_responses), action="field_processing_complete", business_context="webhook_processing")
            return field_responses
        except Exception as e:
            if isinstance(e, WebhookPayloadError):
                raise
            raise WebhookPayloadError(f"Error processing form responses: {e!s}") from e

    async def _parse_field_answer(self, answer: dict[str, Any]) -> FormFieldResponse | None:
        """Parse a single field answer into a structured response.

        Args:
            answer: Raw answer data from form response.

        Returns:
            Parsed field response or None if parsing fails.
        """
        try:
            field_info = answer.get('field', {})
            field_id = field_info.get('id')
            field_type = field_info.get('type')
            field_ref = field_info.get('ref')
            if not field_id or not field_type:
                logger.warning("Missing field ID or type", answer=answer, action="field_validation_missing")
                return None
            question = field_info.get('title', 'Unknown Question')
            answer_value = await self._extract_answer_value(answer, field_type)
            return FormFieldResponse(
                field_id=field_id,
                field_type=field_type,
                question=question,
                answer=answer_value,
                field_ref=field_ref,
            )
        except Exception as e:
            logger.error("Error parsing field answer", error=str(e), action="field_parse_failure")
            return None

    async def _extract_answer_value(self, answer: dict[str, Any], field_type: str) -> Any:
        """Extract the answer value based on field type.

        Args:
            answer: Raw answer data.
            field_type: Type of the form field.

        Returns:
            Extracted answer value appropriate for the field type.
        """
        answer_data = answer.get('answer', answer)
        if field_type in ['short_text', 'long_text']:
            return answer_data.get('text', '')
        elif field_type == 'email':
            return answer_data.get('email') or answer_data.get('text', '')
        elif field_type == 'website':
            return answer_data.get('url') or answer_data.get('text', '')
        elif field_type == 'phone_number':
            return answer_data.get('phone_number') or answer_data.get('text', '')
        elif field_type == 'number':
            return answer_data.get('number')
        elif field_type == 'boolean':
            return answer_data.get('boolean')
        elif field_type in ['choice', 'multiple_choice']:
            choice = answer_data.get('choice', {})
            return {'id': choice.get('id'), 'label': choice.get('label'), 'ref': choice.get('ref')}
        elif field_type == 'choices':
            choices = answer_data.get('choices', [])
            return [{
                'id': c.get('id'),
                'label': c.get('label'),
                'ref': c.get('ref'),
            } for c in choices]
        elif field_type == 'date':
            return answer_data.get('date')
        elif field_type == 'file_url':
            return answer_data.get('file_url')
        elif field_type == 'payment':
            return {'amount': answer_data.get('amount'), 'last4': answer_data.get('last4'), 'name': answer_data.get('name')}
        else:
            logger.warning("Unknown field type, storing raw data", field_type=field_type, action="unknown_field_type")
            return answer_data

    async def _extract_client_identifiers(self, field_responses: list[FormFieldResponse]) -> dict[str, str]:
        """Extract client identifiers from form field responses.

        Uses intelligent field mapping to identify client information including
        names, email, phone, address, and other demographic data.

        Args:
            field_responses: List of processed field responses.

        Returns:
            Dictionary of extracted client identifiers.
        """
        identifiers: dict[str, str] = {}

        def normalize_text(value: str | None) -> str:
            if not value:
                return ''
            lowered = value.strip().lower()
            # Remove accents to match e.g. gênero/sexo variants robustly
            return ''.join(
                c for c in unicodedata.normalize('NFD', lowered)
                if unicodedata.category(c) != 'Mn'
            )

        def matches_any(text: str | None, patterns: list[str]) -> bool:
            norm = normalize_text(text)
            return any(p in norm for p in patterns)

        # 1) Primary detection by field type (works even when no titles/refs contain keywords)
        for fr in field_responses:
            if not fr.answer:
                continue
            ftype = (fr.field_type or '').lower()
            if ftype == 'email' and 'email' not in identifiers:
                identifiers['email'] = str(fr.answer)
                continue
            if ftype == 'phone_number' and 'phone' not in identifiers:
                identifiers['phone'] = str(fr.answer)
                continue

        # Prepare collections to build richer identifiers
        first_name_val: str | None = None
        last_name_val: str | None = None
        full_name_val: str | None = None
        gender_val: str | None = None
        birthday_val: str | None = None
        address_parts: dict[str, str] = {}

        # 2) Secondary detection using ref/title keywords to enrich with names, gender, birthday, address
        patterns = {
            'first_name': ['first name', 'firstname', 'given name', 'nome', 'nome proprio', 'nome de batismo'],
            'last_name': ['last name', 'lastname', 'surname', 'sobrenome', 'apelido'],
            'full_name': ['name', 'full name', 'client name', 'your name', 'nome completo'],
            'email': ['email', 'email address', 'contact email', 'e-mail'],
            'phone': ['phone', 'phone number', 'contact phone', 'mobile', 'whatsapp', 'celular', 'telefone'],
            'company': ['company', 'company name', 'organization', 'business name', 'empresa'],
            'gender': ['gender', 'genero', 'sexo'],
            'birthday': ['birth', 'birthday', 'dob', 'data de nascimento', 'nascimento', 'nasceu'],
            'address_line1': ['address', 'endereco'],
            'address_line2': ['address line 2', 'endereco linha 2', 'complemento'],
            'city': ['city', 'town', 'cidade', 'municipio'],
            'state': ['state', 'region', 'province', 'estado', 'regiao', 'provincia', 'uf'],
            'zip': ['zip', 'postal', 'post code', 'postcode', 'cep', 'codigo postal'],
            'country': ['country', 'pais']
        }

        for fr in field_responses:
            if not fr.answer:
                continue
            field_ref = fr.field_ref or ''
            question = fr.question or ''
            ftype = (fr.field_type or '').lower()

            # Names: prefer explicit full name before first/last
            is_full_name = matches_any(field_ref, patterns['full_name']) or matches_any(question, patterns['full_name'])
            is_first_name = matches_any(field_ref, patterns['first_name']) or matches_any(question, patterns['first_name'])
            is_last_name = matches_any(field_ref, patterns['last_name']) or matches_any(question, patterns['last_name'])

            if not full_name_val and is_full_name:
                full_name_val = str(fr.answer)
                continue
            if not first_name_val and is_first_name and not is_full_name:
                first_name_val = str(fr.answer)
                continue
            if not last_name_val and is_last_name and not is_full_name:
                last_name_val = str(fr.answer)
                continue

            # Gender: prefer choice labels
            if not gender_val and (matches_any(field_ref, patterns['gender']) or matches_any(question, patterns['gender'])):
                if ftype in ['choice', 'multiple_choice'] and isinstance(fr.answer, dict):
                    label = fr.answer.get('label') or fr.answer.get('id') or fr.answer.get('ref')
                    gender_val = str(label) if label else None
                else:
                    gender_val = str(fr.answer)
                # Do not continue; allow address/birthday parsing in same pass

            # Birthday: prefer date type
            if not birthday_val and (ftype == 'date' or matches_any(field_ref, patterns['birthday']) or matches_any(question, patterns['birthday'])):
                birthday_val = str(fr.answer)

            # Address components
            if 'address_line1' not in address_parts and (matches_any(field_ref, patterns['address_line1']) or matches_any(question, patterns['address_line1'])):
                address_parts['address_line1'] = str(fr.answer)
            if 'address_line2' not in address_parts and (matches_any(field_ref, patterns['address_line2']) or matches_any(question, patterns['address_line2'])):
                address_parts['address_line2'] = str(fr.answer)
            if 'city' not in address_parts and (matches_any(field_ref, patterns['city']) or matches_any(question, patterns['city'])):
                address_parts['city'] = str(fr.answer)
            if 'state' not in address_parts and (matches_any(field_ref, patterns['state']) or matches_any(question, patterns['state'])):
                address_parts['state'] = str(fr.answer)
            if 'zip' not in address_parts and (matches_any(field_ref, patterns['zip']) or matches_any(question, patterns['zip'])):
                address_parts['zip'] = str(fr.answer)
            if 'country' not in address_parts and (matches_any(field_ref, patterns['country']) or matches_any(question, patterns['country'])):
                address_parts['country'] = str(fr.answer)

            # Fill gaps for email/phone/company if not captured by type
            if 'email' not in identifiers and (matches_any(field_ref, patterns['email']) or matches_any(question, patterns['email'])):
                identifiers['email'] = str(fr.answer)
            if 'phone' not in identifiers and (matches_any(field_ref, patterns['phone']) or matches_any(question, patterns['phone'])):
                identifiers['phone'] = str(fr.answer)
            if 'company' not in identifiers and (matches_any(field_ref, patterns['company']) or matches_any(question, patterns['company'])):
                identifiers['company'] = str(fr.answer)

        # Resolve name fields
        if full_name_val and not (first_name_val and last_name_val):
            parts = [p for p in (full_name_val or '').split() if p]
            if parts:
                if not first_name_val:
                    first_name_val = parts[0]
                if not last_name_val and len(parts) > 1:
                    last_name_val = ' '.join(parts[1:])
        # If we have first and last, also set a combined name
        if first_name_val and last_name_val and 'name' not in identifiers:
            identifiers['name'] = f"{first_name_val} {last_name_val}".strip()
        # Provide individual name fields as well for downstream consumers
        if first_name_val:
            identifiers['first_name'] = first_name_val
        if last_name_val:
            identifiers['last_name'] = last_name_val
        if full_name_val and 'name' not in identifiers:
            identifiers['name'] = full_name_val
        # If only first_name was discovered, expose it also as name for backward compatibility
        if 'name' not in identifiers and first_name_val and not last_name_val and not full_name_val:
            identifiers['name'] = first_name_val

        # Add gender and birthday when available
        if gender_val:
            identifiers['gender'] = gender_val
        if birthday_val:
            identifiers['birthday'] = birthday_val

        # Compose full address string if we have any parts
        if address_parts:
            # Save granular parts
            for key, val in address_parts.items():
                if val:
                    identifiers[key] = val
            # Compose a human-readable address
            ordered = [
                address_parts.get('address_line1'),
                address_parts.get('address_line2'),
                address_parts.get('city'),
                address_parts.get('state'),
                address_parts.get('zip'),
                address_parts.get('country'),
            ]
            composed = ', '.join([v for v in ordered if v])
            if composed:
                identifiers['address'] = composed

        logger.info("Client identifiers extracted", identifier_keys=list(identifiers.keys()), action="client_identifiers_extracted", business_context="client_onboarding")
        return identifiers

    async def _extract_metadata(self, payload_dict: dict[str, Any]) -> dict[str, Any]:
        """Extract metadata from webhook payload.

        Args:
            payload_dict: Raw webhook payload.

        Returns:
            Dictionary of extracted metadata.
        """
        form_response = payload_dict.get('form_response', {})
        metadata = {
            'webhook_received_at': datetime.now().isoformat(),
            'typeform_event_id': payload_dict.get('event_id'),
            'typeform_event_type': payload_dict.get('event_type'),
            'form_response_id': form_response.get('response_id'),
            'landed_at': form_response.get('landed_at'),
            'calculated_score': form_response.get('calculated', {}).get('score'),
            'hidden_fields': form_response.get('hidden', {}),
            'variables': form_response.get('variables', []),
        }
        return {k: v for k, v in metadata.items() if v is not None}

    async def store_form_response(self, processed_data: ProcessedWebhookData) -> str:
        """Store processed form response data in the database.

        Args:
            processed_data: Processed webhook data to store.

        Returns:
            Response token of the stored form response.

        Raises:
            OnboardingFormNotFoundError: If the form is not found.
            DatabaseOperationError: For database storage errors.
        """
        try:
            form = await self.uow.onboarding_forms.get_by_typeform_id(processed_data.form_id)
            if not form:
                raise OnboardingFormNotFoundError(f"Form not found: {processed_data.form_id}")

            answers_by_ref: dict[str, dict[str, Any]] = {}
            answers_without_ref: list[dict[str, Any]] = []
            for fr in processed_data.field_responses:
                answer_entry: dict[str, Any] = {
                    "field": {
                        "id": fr.field_id,
                        "type": fr.field_type,
                        "ref": fr.field_ref,
                    }
                }
                if fr.field_type in ["short_text", "long_text", "website", "phone_number"]:
                    answer_entry["type"] = "text"
                    answer_entry["text"] = fr.answer
                elif fr.field_type == "email":
                    answer_entry["type"] = "email"
                    answer_entry["email"] = fr.answer
                elif fr.field_type == "number":
                    answer_entry["type"] = "number"
                    answer_entry["number"] = fr.answer
                else:
                    answer_entry["type"] = fr.field_type
                    answer_entry["answer"] = fr.answer
                if fr.field_ref:
                    answers_by_ref[fr.field_ref] = answer_entry
                else:
                    answers_without_ref.append(answer_entry)

            reconstructed_answers: list[dict[str, Any]] = []
            reconstructed_answers.extend(answers_without_ref)
            reconstructed_answers.extend(answers_by_ref.values())

            response_data = {
                'event_id': processed_data.event_id,
                'event_type': processed_data.event_type,
                'form_id': processed_data.form_id,
                'response_token': processed_data.response_token,
                'submitted_at': processed_data.submitted_at.isoformat(),
                'answers': reconstructed_answers,
                'field_responses': [
                    {
                        'field_id': fr.field_id,
                        'field_type': fr.field_type,
                        'question': fr.question,
                        'answer': fr.answer,
                        'field_ref': fr.field_ref,
                    }
                    for fr in processed_data.field_responses
                ],
                'client_identifiers': processed_data.client_identifiers,
                'metadata': processed_data.metadata,
            }

            form_response = FormResponse(
                form_id=form.id,
                response_id=processed_data.response_token,
                response_data=response_data,
                client_identifiers=processed_data.client_identifiers,
                submitted_at=processed_data.submitted_at,
            )
            await self.uow.form_responses.add(form_response)
            await self.uow.commit()
            logger.info("Form response stored", response_id=form_response.id, form_id=form.id, action="form_response_stored")
            return processed_data.response_token
        except Exception as e:
            await self.uow.rollback()
            if isinstance(e, OnboardingFormNotFoundError | DatabaseOperationError):
                raise
            error_msg = f"Error storing form response: {e!s}"
            logger.error(
                "Error storing form response",
                error=str(e),
                action="form_response_storage_error",
                exc_info=True
            )
            raise DatabaseOperationError("form_response_creation", "form_response", error_msg) from e





