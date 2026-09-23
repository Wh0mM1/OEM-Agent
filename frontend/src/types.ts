export type StageType =
  | 'new_lead'
  | 'ongoing_pipeline'
  | 'booked_vehicle'
  | 'post_purchase_service'
  | 'ambiguous';

export interface ToolChipData {
  tool_name: string;
  status: 'success' | 'error' | 'in_progress';
  label: string;
  data?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  stage?: StageType;
  tool_chips?: ToolChipData[];
  timestamp: string;
}

export interface ChatThread {
  id: string;
  title: string;
  createdAt: number;
  lastStage: StageType;
  messages: ChatMessage[];
}

export interface CrmRecords {
  leads: any[];
  deals: any[];
  cases: any[];
}
