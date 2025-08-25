import { z } from 'zod';
import { 
  PipelineOnlineEvent,
  FileProcessingEvent,
  FileCompletedEvent,
  FileFailedEvent,
  StatusUpdateEvent
} from './socket';

// Zod schemas for runtime validation
export const FileInfoSchema = z.object({
  name: z.string(),
  id: z.string().optional(),
  size: z.number().optional(),
  mime_type: z.string().optional(),
  started_at: z.string().optional(),
  completed_at: z.string().optional()
});

export const ProcessingResultsSchema = z.object({
  chunks_created: z.number(),
  embeddings_generated: z.number(),
  processing_duration: z.number(),
  content_length: z.number()
});

export const ProcessingErrorSchema = z.object({
  type: z.string(),
  message: z.string(),
  stage: z.enum(['extraction', 'chunking', 'embedding', 'storing']),
  retryable: z.boolean()
});

export const PipelineOnlineEventSchema = z.object({
  pipeline_id: z.string(),
  pipeline_type: z.enum(['google_drive', 'local_files']),
  status: z.literal('online'),
  started_at: z.string(),
  check_interval: z.number(),
  watch_location: z.string()
});

export const FileProcessingEventSchema = z.object({
  pipeline_id: z.string(),
  file: FileInfoSchema,
  processing_stage: z.enum(['extraction', 'chunking', 'embedding', 'storing']),
  estimated_duration: z.number().optional(),
  timestamp: z.string()
});

export const FileCompletedEventSchema = z.object({
  pipeline_id: z.string(),
  file: FileInfoSchema,
  results: ProcessingResultsSchema,
  success: z.literal(true),
  timestamp: z.string()
});

export const FileFailedEventSchema = z.object({
  pipeline_id: z.string(),
  file: FileInfoSchema,
  error: ProcessingErrorSchema,
  success: z.literal(false),
  timestamp: z.string()
});

// Validation functions
export function validatePipelineOnlineEvent(data: unknown): data is PipelineOnlineEvent {
  try {
    PipelineOnlineEventSchema.parse(data);
    return true;
  } catch {
    return false;
  }
}

export function validateFileProcessingEvent(data: unknown): data is FileProcessingEvent {
  try {
    FileProcessingEventSchema.parse(data);
    return true;
  } catch {
    return false;
  }
}

export function validateFileCompletedEvent(data: unknown): data is FileCompletedEvent {
  try {
    FileCompletedEventSchema.parse(data);
    return true;
  } catch {
    return false;
  }
}

export function validateFileFailedEvent(data: unknown): data is FileFailedEvent {
  try {
    FileFailedEventSchema.parse(data);
    return true;
  } catch {
    return false;
  }
}

// Generic event validator
export function createEventValidator<T>(schema: z.ZodSchema<T>) {
  return (data: unknown): data is T => {
    try {
      schema.parse(data);
      return true;
    } catch (error) {
      console.warn('[SOCKET-VALIDATION] Invalid event data:', error);
      return false;
    }
  };
}

// Event sanitization
export function sanitizeEventData<T>(data: T, allowedFields: (keyof T)[]): Partial<T> {
  const sanitized: Partial<T> = {};
  
  allowedFields.forEach(field => {
    if (field in data) {
      sanitized[field] = data[field];
    }
  });
  
  return sanitized;
}