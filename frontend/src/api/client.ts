import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface TestCase {
  name: string;
  description: string;
  category: "happy_path" | "edge_case" | "error_case";
  inputs?: string;
  expected_output?: string;
}

export interface AgentStep {
  agent: string;
  status: "completed" | "failed";
  output_summary: string;
}

export interface GenerateTestRequest {
  code: string;
  language: "python" | "javascript" | "typescript";
  framework?: string;
}

export interface GenerateTestResponse {
  analysis: string;
  test_cases: TestCase[];
  test_code: string;
  final_tests: string;
  agent_steps: AgentStep[];
  language: string;
  framework: string;
}

export async function generateTests(
  payload: GenerateTestRequest
): Promise<GenerateTestResponse> {
  const response = await axios.post<GenerateTestResponse>(
    `${BASE_URL}/api/generate-tests`,
    payload,
    { headers: { "Content-Type": "application/json" } }
  );
  return response.data;
}
