import { lazy } from "react";
import { Route } from "react-router-dom";
import { AuthorizationAdminRoute } from "../components/authorization-admin-route";

const TeamsPage = lazy(() => import("@/pages/TeamsPage"));
const SharedWithMePage = lazy(() => import("@/pages/SharedWithMePage"));

export const CustomRoutesStorePages = () => {
  return (
    <>
      <Route path="teams" element={<TeamsPage />} />
      <Route path="shared-with-me" element={<SharedWithMePage />} />
      <Route
        path="admin/teams"
        element={
          <AuthorizationAdminRoute>
            <TeamsPage adminMode />
          </AuthorizationAdminRoute>
        }
      />
    </>
  );
};

export default CustomRoutesStorePages;
