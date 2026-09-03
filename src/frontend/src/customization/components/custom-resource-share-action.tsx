import { type MouseEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import ForwardedIconComponent from "@/components/common/genericIconComponent";
import { Button } from "@/components/ui/button";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { usePermissions } from "@/contexts/permissionsContext";
import { useGetAuthorizationCapabilities } from "@/controllers/API/queries/authorization";
import ResourceShareDialog from "./resource-share-dialog";

export type CustomShareResourceType =
  | "deployment"
  | "project"
  | "knowledge_base"
  | "file";

export type CustomShareResourceSubtype = "knowledge_base" | "memory";

export interface CustomResourceShareActionProps {
  resourceId: string;
  resourceType: CustomShareResourceType;
  resourceSubtype?: CustomShareResourceSubtype;
  resourceName?: string;
  /** Compact actions use only an icon; headers may request a text label. */
  display?: "icon" | "label" | "menu";
}

export default function CustomResourceShareAction({
  resourceId,
  resourceType,
  resourceName,
  display = "menu",
}: CustomResourceShareActionProps) {
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
    resourceType !== "project" ||
    isUnavailable ||
    !supported ||
    !capability(resourceId, "can_manage_shares")
  ) {
    return null;
  }

  const openDialog = (event: MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setOpen(true);
  };

  return (
    <>
      {display === "menu" ? (
        <DropdownMenuItem
          className="cursor-pointer text-xs"
          data-testid={`share-project-${resourceId}`}
          onSelect={(event) => event.preventDefault()}
          onClick={openDialog}
        >
          <ForwardedIconComponent
            name="Share2"
            aria-hidden="true"
            className="mr-2 h-4 w-4"
          />
          {t("misc.share")}
        </DropdownMenuItem>
      ) : (
        <Button
          type="button"
          variant="ghost"
          size={display === "icon" ? "icon" : "sm"}
          aria-label={t("sharing.action.for", { resource: resourceName })}
          onClick={openDialog}
        >
          <ForwardedIconComponent name="Share2" aria-hidden="true" />
          {display === "label" ? t("misc.share") : null}
        </Button>
      )}
      <ResourceShareDialog
        open={open}
        onOpenChange={setOpen}
        resourceType="project"
        resourceId={resourceId}
        resourceName={resourceName}
      />
    </>
  );
}
