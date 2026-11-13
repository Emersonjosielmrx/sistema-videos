import re
with open('D:/hipercool-refactor/cmd/server/agentprofiles.go', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure CustomTags are correctly populated in queries
content = content.replace("SELECT id, name, product, system_prompt, initial_context, voice, tts_default, wake_word, meet_mode, kind, trigger, tone, guardrails, knowledge_base, escalation_keywords, handoff_message, background_noise, background_noise_volume, ai_provider, ai_model, instance_name, listen_audio, reply_audio, voice_id, vision_enabled, automations, created_at", "SELECT id, name, product, system_prompt, initial_context, voice, tts_default, wake_word, meet_mode, kind, trigger, tone, guardrails, knowledge_base, escalation_keywords, handoff_message, background_noise, background_noise_volume, ai_provider, ai_model, instance_name, listen_audio, reply_audio, voice_id, vision_enabled, automations, custom_tags, custom_alerts, created_at")

with open('D:/hipercool-refactor/cmd/server/agentprofiles.go', 'w', encoding='utf-8') as f:
    f.write(content)
