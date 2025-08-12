from __future__ import annotations

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.core.domain.models.form_response import FormResponse
from src.contexts.client_onboarding.core.services.exceptions import (
    WebhookPayloadError,
    FormResponseProcessingError,
    OnboardingFormNotFoundError,
    DatabaseOperationError,
)
from src.contexts.client_onboarding.core.services.webhooks.security import WebhookSecurityVerifier

logger = logging.getLogger(__name__)


@dataclass
class FormFieldResponse:
    field_id: str
    field_type: str
    question: str
    answer: Any
    field_ref: Optional[str] = None


@dataclass
class ProcessedWebhookData:
    event_id: str
    event_type: str
    form_id: str
    response_token: str
    submitted_at: datetime
    field_responses: List[FormFieldResponse]
    metadata: Dict[str, Any]
    client_identifiers: Dict[str, str]


class WebhookPayloadProcessor:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def process_webhook_payload(self, payload_dict: Dict[str, Any]) -> ProcessedWebhookData:
        try:
            logger.info(f"Processing webhook payload for event: {payload_dict.get('event_id', 'unknown')}")
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
            error_msg = f"Unexpected error processing webhook payload: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise FormResponseProcessingError("unknown", "payload_processing", error_msg) from e

    async def _extract_event_info(self, payload_dict: Dict[str, Any]) -> Dict[str, Any]:
        try:
            form_response = payload_dict.get('form_response', {})
            submitted_at_str = form_response.get('submitted_at')
            if not submitted_at_str:
                raise WebhookPayloadError("Missing submitted_at timestamp")
            try:
                submitted_at = datetime.fromisoformat(submitted_at_str.replace('Z', '+00:00'))
                submitted_at = submitted_at.astimezone(timezone.utc).replace(tzinfo=None)
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
            raise WebhookPayloadError(f"Error extracting event info: {str(e)}") from e

    async def _verify_form_exists(self, form_id: str) -> None:
        try:
            form = await self.uow.onboarding_forms.get_by_typeform_id(form_id)
            if not form:
                raise OnboardingFormNotFoundError(f"Form not found: {form_id}")
            logger.debug(f"Verified form exists: {form_id} (DB ID: {form.id})")
        except Exception as e:
            if isinstance(e, OnboardingFormNotFoundError):
                raise
            raise DatabaseOperationError("form_verification", "onboarding_form", str(e)) from e

    async def _process_form_responses(self, form_response: Dict[str, Any]) -> List[FormFieldResponse]:
        try:
            answers = form_response.get('answers', [])
            if not isinstance(answers, list):
                raise WebhookPayloadError("Form answers must be a list")
            field_responses: List[FormFieldResponse] = []
            for answer in answers:
                if not isinstance(answer, dict):
                    logger.warning(f"Skipping malformed answer: {answer}")
                    continue
                try:
                    field_response = await self._parse_field_answer(answer)
                    if field_response:
                        field_responses.append(field_response)
                except Exception as e:
                    logger.warning(f"Error parsing field answer: {e}, answer: {answer}")
                    continue
            logger.debug(f"Processed {len(field_responses)} field responses")
            return field_responses
        except Exception as e:
            if isinstance(e, WebhookPayloadError):
                raise
            raise WebhookPayloadError(f"Error processing form responses: {str(e)}") from e

    async def _parse_field_answer(self, answer: Dict[str, Any]) -> Optional[FormFieldResponse]:
        try:
            field_info = answer.get('field', {})
            field_id = field_info.get('id')
            field_type = field_info.get('type')
            field_ref = field_info.get('ref')
            if not field_id or not field_type:
                logger.warning(f"Missing field ID or type: {answer}")
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
            logger.error(f"Error parsing field answer: {e}")
            return None

    async def _extract_answer_value(self, answer: Dict[str, Any], field_type: str) -> Any:
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
            logger.warning(f"Unknown field type: {field_type}, storing raw data")
            return answer_data

    async def _extract_client_identifiers(self, field_responses: List[FormFieldResponse]) -> Dict[str, str]:
        identifiers: Dict[str, str] = {}
        identifier_patterns = {
            'name': ['name', 'full_name', 'client_name', 'your_name'],
            'email': ['email', 'email_address', 'contact_email'],
            'phone': ['phone', 'phone_number', 'contact_phone', 'mobile'],
            'company': ['company', 'company_name', 'organization', 'business_name'],
        }
        for field_response in field_responses:
            field_ref = (field_response.field_ref or '').lower()
            question = field_response.question.lower()
            for identifier_type, patterns in identifier_patterns.items():
                if any(pattern in field_ref or pattern in question for pattern in patterns):
                    if field_response.answer:
                        identifiers[identifier_type] = str(field_response.answer)
                        break
        logger.debug(f"Extracted client identifiers: {list(identifiers.keys())}")
        return identifiers

    async def _extract_metadata(self, payload_dict: Dict[str, Any]) -> Dict[str, Any]:
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
        try:
            form = await self.uow.onboarding_forms.get_by_typeform_id(processed_data.form_id)
            if not form:
                raise OnboardingFormNotFoundError(f"Form not found: {processed_data.form_id}")

            answers_by_ref: Dict[str, Dict[str, Any]] = {}
            answers_without_ref: List[Dict[str, Any]] = []
            for fr in processed_data.field_responses:
                answer_entry: Dict[str, Any] = {
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

            reconstructed_answers: List[Dict[str, Any]] = []
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
            logger.info(f"Stored form response: {form_response.id} for form: {form.id}")
            return processed_data.response_token
        except Exception as e:
            await self.uow.rollback()
            if isinstance(e, (OnboardingFormNotFoundError, DatabaseOperationError)):
                raise
            error_msg = f"Error storing form response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DatabaseOperationError("form_response_creation", "form_response", error_msg) from e


class WebhookProcessor:
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory

    async def process_webhook(self, payload: str, headers: Dict[str, str]) -> Tuple[bool, Optional[str], Optional[str]]:
        async with self.uow_factory() as uow:
            try:
                processor = WebhookPayloadProcessor(uow)
                try:
                    payload_dict = json.loads(payload)
                except json.JSONDecodeError as e:
                    return False, f"Invalid JSON payload: {str(e)}", None
                processed_data = await processor.process_webhook_payload(payload_dict)
                response_id = await processor.store_form_response(processed_data)
                try:
                    await WebhookSecurityVerifier.mark_request_processed(payload, headers)
                except Exception:
                    pass
                return True, None, response_id
            except Exception as e:
                logger.error(f"Webhook processing failed: {str(e)}", exc_info=True)
                return False, str(e), None


async def process_typeform_webhook(payload: str, headers: Dict[str, str], uow_factory) -> Tuple[bool, Optional[str], Optional[str]]:
    processor = WebhookProcessor(uow_factory)
    return await processor.process_webhook(payload, headers)


