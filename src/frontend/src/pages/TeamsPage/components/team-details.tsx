import { useEffect, useId, useState } from "react";
import { useTranslation } from "react-i18next";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  useAddTeamMember,
  useDeleteTeam,
  useGetTeam,
  useGetTeamMembers,
  useRemoveTeamMember,
  useUpdateTeam,
  useUpdateTeamMemberRole,
} from "@/controllers/API/queries/teams";
import type { AuthorizationTeam, TeamRole } from "@/types/authz";
import { extractApiErrorMessages } from "@/utils/apiError";
import { TeamMemberPicker } from "./team-member-picker";

const allRoles: TeamRole[] = ["admin", "maintainer", "user"];

export function TeamDetails({
  teamId,
  onDeleted,
}: {
  teamId: string;
  onDeleted: () => void;
}) {
  const { t } = useTranslation();
  const nameId = useId();
  const domainId = useId();
  const descriptionId = useId();
  const [memberOffset, setMemberOffset] = useState(0);
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [description, setDescription] = useState("");
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const teamQuery = useGetTeam(teamId);
  const membersQuery = useGetTeamMembers({
    teamId,
    limit: 50,
    offset: memberOffset,
  });
  const team = teamQuery.data;

  useEffect(() => {
    if (!team) return;
    setName(team.team_name);
    setDomain(team.adom_name);
    setDescription(team.description ?? "");
  }, [team]);

  const mutationError = (requestError: unknown) =>
    setError(extractApiErrorMessages(requestError).join(" "));
  const updateTeam = useUpdateTeam({ onError: mutationError });
  const addMember = useAddTeamMember({ onError: mutationError });
  const updateRole = useUpdateTeamMemberRole({ onError: mutationError });
  const removeMember = useRemoveTeamMember({ onError: mutationError });
  const deleteTeam = useDeleteTeam({
    onSuccess: () => {
      setDeleteOpen(false);
      onDeleted();
    },
    onError: mutationError,
  });

  if (teamQuery.isLoading) return <p role="status">{t("teams.loading")}</p>;
  if (teamQuery.isError || !team) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{t("teams.error")}</AlertDescription>
      </Alert>
    );
  }

  const canEdit = team.capabilities.can_update;
  const canEditDirectoryMapping = team.capabilities.can_set_active;
  const canAdd = team.capabilities.can_add_user_member;
  const allowedAddRoles = team.capabilities.can_add_privileged_member
    ? allRoles
    : (["user"] as TeamRole[]);

  return (
    <section
      className="space-y-5"
      data-testid={`team-details-${team.id}`}
      aria-labelledby={`team-heading-${team.id}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id={`team-heading-${team.id}`} className="text-xl font-semibold">
            {team.team_name}
          </h2>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge
              variant={team.is_active ? "successStatic" : "secondaryStatic"}
            >
              {team.is_active
                ? t("teams.status.active")
                : t("teams.status.inactive")}
            </Badge>
            {team.current_user_role && (
              <Badge variant="outline">
                {t(`teams.role.${team.current_user_role}`)}
              </Badge>
            )}
          </div>
        </div>
        {team.capabilities.can_delete && (
          <Button
            type="button"
            variant="destructive"
            size="sm"
            onClick={() => setDeleteOpen(true)}
          >
            {t("teams.delete")}
          </Button>
        )}
      </div>

      {team.inactivation_reason === "no_active_admin" && (
        <Alert>
          <AlertDescription>{t("teams.noActiveAdmin")}</AlertDescription>
        </Alert>
      )}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <section aria-labelledby="team-details-heading" className="space-y-3">
        <h3 id="team-details-heading" className="font-semibold">
          {t("teams.details")}
        </h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor={nameId}>{t("teams.name")}</Label>
            <Input
              id={nameId}
              value={name}
              disabled={!canEdit}
              onChange={(event) => setName(event.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor={domainId}>{t("teams.domain")}</Label>
            <Input
              id={domainId}
              value={domain}
              disabled={!canEditDirectoryMapping}
              onChange={(event) => setDomain(event.target.value)}
            />
          </div>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor={descriptionId}>{t("teams.description")}</Label>
          <Textarea
            id={descriptionId}
            value={description}
            disabled={!canEdit}
            onChange={(event) => setDescription(event.target.value)}
          />
        </div>
        {team.capabilities.can_set_active && (
          <div className="flex items-center gap-3">
            <Switch
              id={`team-active-${team.id}`}
              checked={team.is_active}
              disabled={updateTeam.isPending}
              onCheckedChange={(checked) => {
                setError(null);
                updateTeam.mutate({ teamId, data: { is_active: checked } });
              }}
            />
            <Label htmlFor={`team-active-${team.id}`}>
              {t("teams.active")}
            </Label>
          </div>
        )}
        {canEdit && (
          <Button
            type="button"
            loading={updateTeam.isPending}
            disabled={!name.trim() || !domain.trim()}
            onClick={() => {
              setError(null);
              updateTeam.mutate({
                teamId,
                data: {
                  team_name: name.trim(),
                  description: description.trim() || null,
                  ...(canEditDirectoryMapping
                    ? { adom_name: domain.trim() }
                    : {}),
                },
              });
            }}
          >
            {t("teams.save")}
          </Button>
        )}
      </section>

      <section
        aria-labelledby="team-members-heading"
        className="space-y-3 border-t pt-4"
      >
        <h3 id="team-members-heading" className="font-semibold">
          {t("teams.members")}
        </h3>
        {canAdd && (
          <TeamMemberPicker
            teamId={teamId}
            allowedRoles={allowedAddRoles}
            excludedUserIds={membersQuery.data?.map((member) => member.user_id)}
            disabled={addMember.isPending}
            onAdd={(recipient, role) => {
              setError(null);
              addMember.mutate({
                teamId,
                member: { user_id: recipient.id, role },
              });
            }}
          />
        )}
        {membersQuery.isLoading ? (
          <p role="status">{t("teams.loading")}</p>
        ) : membersQuery.isError ? (
          <Alert variant="destructive">
            <AlertDescription>{t("teams.error")}</AlertDescription>
          </Alert>
        ) : membersQuery.data?.length ? (
          <ul className="divide-y rounded-lg border">
            {membersQuery.data.map((member) => {
              const manual = member.source === "manual";
              const canChange = team.capabilities.can_change_roles;
              const canRemove =
                manual &&
                (member.role === "user"
                  ? team.capabilities.can_remove_user_member
                  : team.capabilities.can_change_roles);
              const memberName = member.display_name ?? member.user_id;
              return (
                <li
                  key={member.id}
                  className="flex flex-wrap items-center gap-3 p-3"
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">
                      {memberName}
                    </div>
                    <Badge
                      variant={manual ? "secondaryStatic" : "outline"}
                      size="tag"
                      className="mt-1"
                    >
                      {manual
                        ? t("teams.source.manual")
                        : t("teams.source.external")}
                    </Badge>
                  </div>
                  <Select
                    value={member.role}
                    disabled={!canChange || updateRole.isPending}
                    onValueChange={(value) => {
                      setError(null);
                      updateRole.mutate({
                        teamId,
                        userId: member.user_id,
                        role: value as TeamRole,
                      });
                    }}
                  >
                    <SelectTrigger
                      className="w-36"
                      aria-label={t("teams.role")}
                    >
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {allRoles.map((role) => (
                        <SelectItem key={role} value={role}>
                          {t(`teams.role.${role}`)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {canRemove && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="text-destructive"
                      loading={removeMember.isPending}
                      aria-label={t("teams.removeMember", {
                        member: memberName,
                      })}
                      onClick={() => {
                        setError(null);
                        removeMember.mutate({ teamId, userId: member.user_id });
                      }}
                    >
                      {t("sharing.remove")}
                    </Button>
                  )}
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">
            {t("teams.noMembers")}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={memberOffset === 0}
            onClick={() =>
              setMemberOffset((offset) => Math.max(0, offset - 50))
            }
          >
            {t("teams.previous")}
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={(membersQuery.data?.length ?? 0) < 50}
            onClick={() => setMemberOffset((offset) => offset + 50)}
          >
            {t("teams.next")}
          </Button>
        </div>
      </section>

      <DeleteTeamDialog
        team={team}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        loading={deleteTeam.isPending}
        onDelete={() => deleteTeam.mutate({ teamId })}
      />
    </section>
  );
}

function DeleteTeamDialog({
  team,
  open,
  onOpenChange,
  loading,
  onDelete,
}: {
  team: AuthorizationTeam;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  loading: boolean;
  onDelete: () => void;
}) {
  const { t } = useTranslation();
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {t("teams.deleteConfirmTitle", { teamName: team.team_name })}
          </DialogTitle>
          <DialogDescription>
            {t("teams.deleteConfirmDescription")}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            {t("teams.cancel")}
          </Button>
          <Button
            type="button"
            variant="destructive"
            loading={loading}
            onClick={onDelete}
          >
            {t("teams.deleteConfirm")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
