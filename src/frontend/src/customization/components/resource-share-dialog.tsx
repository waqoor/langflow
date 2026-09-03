import { useEffect, useId, useState } from "react";
import { useTranslation } from "react-i18next";
import ForwardedIconComponent from "@/components/common/genericIconComponent";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  useGetAuthorizationCapabilities,
  useSearchAuthorizationRecipients,
} from "@/controllers/API/queries/authorization";
import {
  useCreateShare,
  useDeleteShare,
  useGetShareSummary,
  useUpdateShare,
} from "@/controllers/API/queries/shares";
import type {
  AuthorizationRecipient,
  AuthorizationShare,
  ShareDialogPermission,
  ShareRecipientType,
  ShareResourceType,
} from "@/types/authz";
import { extractApiErrorMessages } from "@/utils/apiError";
import { cn } from "@/utils/utils";

interface ResourceShareDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resourceType: ShareResourceType;
  resourceId: string;
  resourceName?: string;
}

function useDebouncedValue(value: string, delay = 300): string {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [delay, value]);
  return debounced;
}

const permissionOptions: ShareDialogPermission[] = ["execute", "write"];

function permissionLabelKey(permission: ShareDialogPermission) {
  return permission === "execute"
    ? "sharing.mode.use.label"
    : "sharing.mode.edit.label";
}

function permissionDescriptionKey(permission: ShareDialogPermission) {
  return permission === "execute"
    ? "sharing.mode.use.description"
    : "sharing.mode.edit.description";
}

function GrantRow({
  grant,
  resourceType,
  resourceId,
}: {
  grant: AuthorizationShare;
  resourceType: ShareResourceType;
  resourceId: string;
}) {
  const { t } = useTranslation();
  const [error, setError] = useState<string | null>(null);
  const updateShare = useUpdateShare({
    onError: (requestError) =>
      setError(extractApiErrorMessages(requestError).join(" ")),
  });
  const deleteShare = useDeleteShare({
    onError: (requestError) =>
      setError(extractApiErrorMessages(requestError).join(" ")),
  });
  const currentPermission: ShareDialogPermission =
    grant.permission_level === "write" ? "write" : "execute";
  const target = grant.target_name ?? t("sharing.unknownRecipient");

  return (
    <li
      className="rounded-lg border border-border p-3"
      data-testid={`share-grant-${grant.id}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium">{target}</div>
          <Badge variant="secondaryStatic" size="tag" className="mt-1">
            {grant.scope === "team"
              ? t("sharing.recipient.team")
              : t("sharing.recipient.user")}
          </Badge>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="text-destructive"
          loading={deleteShare.isPending}
          aria-label={t("sharing.revoke.target", { target })}
          onClick={() => {
            setError(null);
            deleteShare.mutate({
              shareId: grant.id,
              revision: grant.revision,
              resourceType,
              resourceId,
            });
          }}
        >
          {t("sharing.remove")}
        </Button>
      </div>
      <RadioGroup
        className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2"
        value={currentPermission}
        aria-label={t("sharing.permission.for", { target })}
        disabled={updateShare.isPending || deleteShare.isPending}
        onValueChange={(value) => {
          const permission = value as ShareDialogPermission;
          if (permission === currentPermission) return;
          setError(null);
          updateShare.mutate({
            shareId: grant.id,
            revision: grant.revision,
            resourceType,
            resourceId,
            permission,
          });
        }}
      >
        {permissionOptions.map((permission) => (
          <Label
            key={permission}
            className="flex cursor-pointer items-start gap-2 rounded-md border p-2 text-xs"
          >
            <RadioGroupItem value={permission} />
            <span>{t(permissionLabelKey(permission))}</span>
          </Label>
        ))}
      </RadioGroup>
      {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
    </li>
  );
}

export function ResourceShareDialog({
  open,
  onOpenChange,
  resourceType,
  resourceId,
  resourceName,
}: ResourceShareDialogProps) {
  const { t } = useTranslation();
  const searchId = useId();
  const [recipientType, setRecipientType] =
    useState<ShareRecipientType>("user");
  const [search, setSearch] = useState("");
  const [selectedRecipient, setSelectedRecipient] =
    useState<AuthorizationRecipient | null>(null);
  const [permission, setPermission] =
    useState<ShareDialogPermission>("execute");
  const [error, setError] = useState<string | null>(null);
  const debouncedSearch = useDebouncedValue(search);
  const capabilities = useGetAuthorizationCapabilities({ enabled: open });
  const summary = useGetShareSummary(
    { resourceType, resourceId },
    { enabled: open },
  );
  const recipients = useSearchAuthorizationRecipients(
    {
      purpose: "share",
      kind: recipientType,
      query: debouncedSearch,
      resourceType,
      resourceId,
    },
    { enabled: open },
  );
  const createShare = useCreateShare({
    onSuccess: () => {
      setSearch("");
      setSelectedRecipient(null);
      setError(null);
    },
    onError: (requestError) =>
      setError(extractApiErrorMessages(requestError).join(" ")),
  });

  useEffect(() => {
    setSelectedRecipient(null);
    setSearch("");
  }, [recipientType]);

  const contractReady = Boolean(
    capabilities.data?.enforcement_active &&
      capabilities.data.service_ready &&
      capabilities.data.user_team_sharing_supported &&
      capabilities.data.share_modes.includes("execute") &&
      capabilities.data.share_modes.includes("write"),
  );
  const canManage = contractReady && summary.data?.can_manage_shares === true;
  const titleName =
    resourceName || summary.data?.display_name || t("sharing.resource.unnamed");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-h-[88vh] max-w-2xl overflow-y-auto"
        data-testid="resource-share-dialog"
      >
        <DialogHeader>
          <DialogTitle>
            {t("sharing.dialog.title", { resourceName: titleName })}
          </DialogTitle>
          <DialogDescription>
            {t("sharing.dialog.description")}
          </DialogDescription>
        </DialogHeader>

        {resourceType === "project" && (
          <Alert>
            <AlertDescription>
              {t("sharing.project.inheritance")}
            </AlertDescription>
          </Alert>
        )}

        {(capabilities.isLoading || summary.isLoading) && (
          <div
            className="flex items-center gap-2 py-6 text-sm text-muted-foreground"
            role="status"
          >
            <ForwardedIconComponent name="Loader2" className="animate-spin" />
            {t("sharing.loading")}
          </div>
        )}

        {(capabilities.isError ||
          summary.isError ||
          (!capabilities.isLoading && !contractReady)) && (
          <Alert variant="destructive">
            <AlertDescription>{t("sharing.unavailable")}</AlertDescription>
          </Alert>
        )}

        {!summary.isLoading &&
          contractReady &&
          !summary.data?.can_manage_shares && (
            <Alert variant="destructive">
              <AlertDescription>{t("sharing.notAllowed")}</AlertDescription>
            </Alert>
          )}

        {canManage && (
          <>
            <section
              aria-labelledby="share-recipient-heading"
              className="space-y-3"
            >
              <h3
                id="share-recipient-heading"
                className="text-sm font-semibold"
              >
                {t("sharing.addRecipient")}
              </h3>
              <RadioGroup
                value={recipientType}
                onValueChange={(value) =>
                  setRecipientType(value as ShareRecipientType)
                }
                className="grid grid-cols-2"
                aria-label={t("sharing.recipientType")}
              >
                {(["user", "team"] as ShareRecipientType[]).map((kind) => (
                  <Label
                    key={kind}
                    className="flex cursor-pointer items-center gap-2 rounded-md border p-3"
                  >
                    <RadioGroupItem value={kind} />
                    {t(`sharing.recipient.${kind}`)}
                  </Label>
                ))}
              </RadioGroup>

              <div className="space-y-1.5">
                <Label htmlFor={searchId}>
                  {t("sharing.searchRecipients")}
                </Label>
                <Input
                  id={searchId}
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setSelectedRecipient(null);
                  }}
                  placeholder={t("sharing.searchPlaceholder", {
                    recipient: t(
                      `sharing.recipient.${recipientType}`,
                    ).toLowerCase(),
                  })}
                  aria-describedby={`${searchId}-hint`}
                />
                <p
                  id={`${searchId}-hint`}
                  className="text-xs text-muted-foreground"
                >
                  {t("sharing.searchHint")}
                </p>
              </div>

              {recipients.isFetching && debouncedSearch.trim().length >= 2 && (
                <p role="status" className="text-sm text-muted-foreground">
                  {t("sharing.searching")}
                </p>
              )}
              {recipients.data?.items && recipients.data.items.length > 0 && (
                <ul className="max-h-40 space-y-1 overflow-y-auto rounded-md border p-1">
                  {recipients.data.items.map((recipient) => (
                    <li key={`${recipient.kind}-${recipient.id}`}>
                      <button
                        type="button"
                        className={cn(
                          "w-full rounded px-3 py-2 text-left text-sm hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                          selectedRecipient?.id === recipient.id && "bg-muted",
                        )}
                        aria-pressed={selectedRecipient?.id === recipient.id}
                        onClick={() => setSelectedRecipient(recipient)}
                      >
                        {recipient.display_name}
                      </button>
                    </li>
                  ))}
                </ul>
              )}

              <RadioGroup
                value={permission}
                onValueChange={(value) =>
                  setPermission(value as ShareDialogPermission)
                }
                className="grid grid-cols-1 gap-2 sm:grid-cols-2"
                aria-label={t("sharing.accessLevel")}
              >
                {permissionOptions.map((option) => (
                  <Label
                    key={option}
                    className={cn(
                      "flex cursor-pointer items-start gap-3 rounded-lg border p-3",
                      permission === option && "border-primary",
                    )}
                  >
                    <RadioGroupItem value={option} />
                    <span>
                      <span className="block text-sm font-medium">
                        {t(permissionLabelKey(option))}
                      </span>
                      <span className="mt-1 block text-xs font-normal text-muted-foreground">
                        {t(permissionDescriptionKey(option))}
                      </span>
                    </span>
                  </Label>
                ))}
              </RadioGroup>

              {recipientType === "team" && selectedRecipient && (
                <p className="text-xs text-muted-foreground">
                  {t("sharing.team.futureMembers")}
                </p>
              )}
              {error && (
                <p role="alert" className="text-sm text-destructive">
                  {error}
                </p>
              )}
              <Button
                type="button"
                className="w-full sm:w-auto"
                disabled={!selectedRecipient}
                loading={createShare.isPending}
                onClick={() => {
                  if (!selectedRecipient) return;
                  setError(null);
                  createShare.mutate({
                    resourceType,
                    resourceId,
                    recipientType,
                    recipientId: selectedRecipient.id,
                    permission,
                  });
                }}
              >
                {t("sharing.save")}
              </Button>
            </section>

            <section
              aria-labelledby="existing-access-heading"
              className="space-y-3 border-t pt-4"
            >
              <h3
                id="existing-access-heading"
                className="text-sm font-semibold"
              >
                {t("sharing.existingAccess")}
              </h3>
              {summary.data?.direct_grants.length ? (
                <ul className="space-y-2">
                  {summary.data.direct_grants.map((grant) => (
                    <GrantRow
                      key={grant.id}
                      grant={grant}
                      resourceType={resourceType}
                      resourceId={resourceId}
                    />
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">
                  {t("sharing.noGrants")}
                </p>
              )}
              {summary.data?.inherited_from_project && (
                <p className="text-xs text-muted-foreground">
                  {t("sharing.inheritedAccess")}
                </p>
              )}
              {summary.data?.additional_access_warning && (
                <Alert>
                  <AlertDescription>
                    {t("sharing.additionalAccessWarning")}
                  </AlertDescription>
                </Alert>
              )}
              {summary.data?.legacy_public_access && (
                <Alert>
                  <AlertDescription>
                    {t("sharing.legacyPublicWarning")}
                  </AlertDescription>
                </Alert>
              )}
            </section>
          </>
        )}

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            {t("common.close")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default ResourceShareDialog;
