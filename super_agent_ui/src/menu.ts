import { MenuIntegrationConfig } from "./types/integration";

export const menuIntegrations: MenuIntegrationConfig[] = [
  {
    id: "server-starter-all-features",
    name: "Server Starter (All Features)",
    features: [
      "agentic_a2a_chat",
      "agentic_chat",
      "human_in_the_loop",
      "agentic_generative_ui",
      "tool_based_generative_ui",
      "shared_state",
      "predictive_state_updates",
    ],
  }
];
