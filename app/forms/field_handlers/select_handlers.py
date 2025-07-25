from typing import Any, Sequence

from wtforms.fields.core import UnboundField

from app.forms.field_handlers.field_handler import FieldHandler
from app.forms.fields import (
    MultipleSelectFieldWithDetailAnswer,
    SelectFieldWithDetailAnswer,
)
from app.questionnaire.dynamic_answer_options import DynamicAnswerOptions
from app.questionnaire.questionnaire_schema import InvalidSchemaConfigurationException
from app.utilities.types import ChoiceType, ChoiceWithDetailAnswer


class SelectHandlerBase(FieldHandler):
    @property
    def choices(self) -> Sequence[ChoiceType]:
        _choices = self._build_dynamic_choices() + self._build_static_choices()
        if not _choices:
            raise InvalidSchemaConfigurationException()
        return _choices

    @property
    def dynamic_options_schema(self) -> dict[str, Any]:
        return self.answer_schema.get("dynamic_options", {})

    def _build_dynamic_choices(self) -> list[ChoiceWithDetailAnswer]:
        if not self.dynamic_options_schema:
            return []

        dynamic_options = DynamicAnswerOptions(
            dynamic_options_schema=self.dynamic_options_schema,
            rule_evaluator=self.rule_evaluator,
            value_source_resolver=self.value_source_resolver,
        )

        return [
            ChoiceWithDetailAnswer(option["value"], option["label"], None)
            for option in dynamic_options.evaluate()
        ]

    def _build_static_choices(self) -> list[ChoiceWithDetailAnswer]:
        choices = []

        for option in self.answer_schema.get("options", []):
            detail_answer_id = option.get("detail_answer", {}).get("id")
            choices.append(
                ChoiceWithDetailAnswer(
                    option["value"], option["label"], detail_answer_id
                )
            )
        return choices


class SelectHandler(SelectHandlerBase):
    MANDATORY_MESSAGE_KEY = "MANDATORY_RADIO"

    @staticmethod
    def coerce_str_unless_none(value: str | None) -> str | None:
        """
        Coerces a value using str() unless that value is None
        :param value: Any value that can be coerced using str() or None
        :return: str(value) or None if value is None
        """
        return str(value) if value is not None else None

    # We use a custom coerce function to avoid a defect where Python NoneType
    # is coerced to the string 'None' which clashes with legitimate Radio field
    # values of 'None'; i.e. there is no way to differentiate between the user
    # not providing an answer and them selecting the 'None' option otherwise.
    # https://github.com/ONSdigital/eq-survey-runner/issues/1013
    # See related WTForms PR: https://github.com/wtforms/wtforms/pull/288
    def get_field(self) -> UnboundField | SelectFieldWithDetailAnswer:
        return SelectFieldWithDetailAnswer(
            label=self.label,
            description=self.guidance,
            choices=self.choices,
            validators=self.validators,
            coerce=self.coerce_str_unless_none,
        )


class SelectMultipleHandler(SelectHandler):
    MANDATORY_MESSAGE_KEY = "MANDATORY_CHECKBOX"

    def get_field(self) -> UnboundField | MultipleSelectFieldWithDetailAnswer:
        return MultipleSelectFieldWithDetailAnswer(
            label=self.label,
            description=self.guidance,
            choices=self.choices,
            validators=self.validators,
        )
