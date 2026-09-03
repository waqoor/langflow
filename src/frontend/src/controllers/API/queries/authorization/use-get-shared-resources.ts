import type { ProjectListType } from "@/pages/MainPage/entities";
import useAuthStore from "@/stores/authStore";
import type { useQueryFunctionType } from "@/types/api";
import type { FlowType } from "@/types/flow";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface SharedResources {
  flows: FlowType[];
  projects: ProjectListType[];
}

export const useGetSharedResources: useQueryFunctionType<
  undefined,
  SharedResources
> = (options) => {
  const { query } = UseRequestProcessor();
  const userId = useAuthStore((state) => state.userData?.id);
  return query(
    ["authorizationSharedResources", userId ?? "anonymous"],
    async () => {
      const [flows, projects] = await Promise.all([
        api.get<FlowType[]>(`${getURL("FLOWS")}/`, {
          params: { get_all: true, shared_only: true },
        }),
        api.get<ProjectListType[]>(`${getURL("PROJECTS")}/`, {
          params: { shared_only: true },
        }),
      ]);
      return { flows: flows.data, projects: projects.data };
    },
    {
      staleTime: 15_000,
      ...options,
      enabled: Boolean(userId) && (options?.enabled ?? true),
    },
  );
};
