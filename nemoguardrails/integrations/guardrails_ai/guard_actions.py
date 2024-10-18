from guardrails import Guard

from nemoguardrails.rails.llm.llmrails import LLMRails


def register_guardrails_guard_actions(rails: LLMRails, guard: Guard, guard_name: str):
    def fix_action(text, metadata={}):
        return guard.validate(llm_output=text, metadata=metadata).validated_output

    def validate_action(text, metadata={}):
        return guard.validate(llm_output=text, metadata=metadata).validation_passed

    rails.register_action(fix_action, f"{guard_name}_fix")
    rails.register_action(validate_action, f"{guard_name}_validate")
    rails.register_action(validate_action, f"{guard_name}_validate")
    rails.register_action(validate_action, f"{guard_name}_validate")
