import "server-only";

import { AgentIntegrationConfig } from "./types/integration";
import { ServerStarterAllFeaturesAgent } from "./server-starter-all-features";

export const agentsIntegrations: AgentIntegrationConfig[] = [
  {
    id: "server-starter-all-features",
    agents: async () => {
      return {
        agentic_a2a_chat: new ServerStarterAllFeaturesAgent({
          url: "http://localhost:8000/agentic_a2a_chat",
        }),
        agentic_chat: new ServerStarterAllFeaturesAgent({
          url: "http://localhost:8000/agentic_chat",
        }),
        human_in_the_loop: new ServerStarterAllFeaturesAgent({
          url: "http://localhost:8000/human_in_the_loop",
        }),
        agentic_generative_ui: new ServerStarterAllFeaturesAgent({
          url: "http://localhost:8000/agentic_generative_ui",
        }),
        tool_based_generative_ui: new ServerStarterAllFeaturesAgent({
          url: "http://localhost:8000/tool_based_generative_ui",
        }),
        shared_state: new ServerStarterAllFeaturesAgent({
          url: "http://localhost:8000/shared_state",
        }),
        predictive_state_updates: new ServerStarterAllFeaturesAgent({
          url: "http://localhost:8000/predictive_state_updates",
        }),
      };
    },
  },
];
