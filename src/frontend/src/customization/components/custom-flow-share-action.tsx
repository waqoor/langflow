import { useState } from "react";
import { useTranslation } from "react-i18next";
import ForwardedIconComponent from "@/components/common/genericIconComponent";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { usePermissions } from "@/contexts/permissionsContext";
import { useGetAuthorizationCapabilities } from "@/controllers/API/queries/authorization";
import type { PermissionResourceType } from "@/types/permissions";
import ResourceShareDialog from "./resource-share-dialog";

interface CustomFlowShareActionProps {
  resourceId: string;
  resourceType: PermissionResourceType;
  resourceName?: string;
  /** Placement hint for overlays: the editor's Share dropdown may use a longer label. */
  menuContext?: "card" | "editor";
}

export default function CustomFlowShareAction({
  resourceId,
  resourceType,
  resourceName,
}: CustomFlowShareActionProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const { capability, isUnavailable } = usePermissions();
  const capabilities = useGetAuthorizationCapabilities();
  const supported = Boolean(
    capabilities.data?.enforcement_active &&
      capabilities.data.service_ready &&
      capabilities.data.user_team_sharing_supported,
  );
  if (
    resourceType !== "flow" ||
    isUnavailable ||
    !supported ||
    !capability(resourceId, "can_manage_shares")
  ) {
    return null;
  }

  return (
    <>
      <DropdownMenuItem
        className="cursor-pointer"
        data-testid={`share-flow-${resourceId}`}
        onSelect={(event) => event.preventDefault()}
        onClick={(event) => {
          event.preventDefault();
          event.stopPropagation();
          setOpen(true);
        }}
      >
        <ForwardedIconComponent
          name="Share2"
          aria-hidden="true"
          className="mr-2 h-4 w-4"
        />
        {t("misc.share")}
      </DropdownMenuItem>
      <ResourceShareDialog
        open={open}
        onOpenChange={setOpen}
        resourceType="flow"
        resourceId={resourceId}
        resourceName={resourceName}
      />
    </>
  );
}
