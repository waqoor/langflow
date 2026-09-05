import { useTranslation } from "react-i18next";
import { HeaderMenuItemButton } from "@/components/core/appHeaderComponent/components/HeaderMenu";
import { useGetAuthorizationCapabilities } from "@/controllers/API/queries/authorization";

export interface CustomAdminPageMenuItemProps {
  onNavigate: (path: string) => void;
}

export const CustomAdminPageMenuItem = ({
  onNavigate,
}: CustomAdminPageMenuItemProps) => {
  const { t } = useTranslation();
  const capabilities = useGetAuthorizationCapabilities();
  if (
    capabilities.isLoading ||
    capabilities.isError ||
    !capabilities.data?.enforcement_active ||
    !capabilities.data.service_ready
  ) {
    return null;
  }
  return (
    <>
      <HeaderMenuItemButton onClick={() => onNavigate("/teams")}>
        <span data-testid="menu-teams-button">
          {t("authz.navigation.teams")}
        </span>
      </HeaderMenuItemButton>
      <HeaderMenuItemButton onClick={() => onNavigate("/shared-with-me")}>
        <span data-testid="menu-shared-with-me-button">
          {t("authz.navigation.sharedWithMe")}
        </span>
      </HeaderMenuItemButton>
      {capabilities.data.can_administer_platform && (
        <HeaderMenuItemButton onClick={() => onNavigate("/admin/teams")}>
          <span data-testid="menu-admin-teams-button">
            {t("authz.navigation.adminTeams")}
          </span>
        </HeaderMenuItemButton>
      )}
    </>
  );
};

export default CustomAdminPageMenuItem;
