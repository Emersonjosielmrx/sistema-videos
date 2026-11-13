export type Button = { label: string; action: 'ai' | 'reply' | 'human'; reply: string }
export type Rule = { text: string; created_at: string; source: string }

export type FlowConfig = {
  store_name: string; store_city: string; store_address: string; store_hours: string; delivery_info: string; business_info: string
  order_mode: 'link' | 'pix' | 'none' | 'agendamento'; menu_url: string; pix_key: string
  prompt: string; learned_rules: Rule[]; model: string; history_limit: number
  menu_enabled: boolean; menu: Record<string, unknown>; button_style: 'enquete' | 'botoes'
  greeting_text: string; buttons_enabled: boolean; buttons_title: string; buttons: Button[]
  audio_action: string; audio_reply: string; image_action: string; image_reply: string
  document_action: string; document_reply: string; other_action: string; other_reply: string
  hours_enabled: boolean; timezone: string; hours: Record<string, string>; closed_action: string; closed_message: string
  pause_on_owner_reply: boolean; pause_minutes: number; owner_off_two_messages: boolean; buffer_seconds: number
  typing: boolean; split_messages: boolean; reply_length: 'curta' | 'media' | 'livre'
  notify_phone: string; notify_handoff: boolean; notify_receipt: boolean; notify_order: boolean
}

export type Flow = {
  id: number; name: string; type: string; template: string; active: boolean; connection_id: number | null
  config: FlowConfig; whatsapp?: { status: string; phone: string }
}

export type Step = { node: string; status: 'ok' | 'skip' | 'stop' | 'error'; info: string; ms?: number }

export type Execution = {
  id: number; flow_id: number; flow_name?: string; direction: string; phone: string; message_type: string
  content: string; agent_response: string; status: string; created_at: string
  metadata: { steps?: Step[]; mode?: string; error?: string; files?: number[]; response_ms?: number }
}
