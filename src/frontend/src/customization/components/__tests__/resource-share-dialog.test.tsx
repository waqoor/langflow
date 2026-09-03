import { fireEvent, render, screen } from "@testing-library/react";
import { axe } from "@/utils/a11y-test";
import { ResourceShareDialog } from "../resource-share-dialog";

const mockCreateShare = jest.fn();
const mockUpdateShare = jest.fn();
const mockDeleteShare = jest.fn();

jest.mock("@/controllers/API/queries/authorization", () => ({
  useGetAuthorizationCapabilities: () => ({
    data: {
      enforcement_active: true,
      service_ready: true,
      user_team_sharing_supported: true,
      share_modes: ["execute", "write"],
    },
    isLoading: false,
    isError: false,
  }),
  useSearchAuthorizationRecipients: () => ({
    data: {
      items: [{ id: "user-2", kind: "user", display_name: "Second User" }],
    },
    isFetching: false,
  }),
}));

jest.mock("@/controllers/API/queries/shares", () => ({
  useGetShareSummary: () => ({
    data: {
      display_name: "Quarterly agent",
      can_manage_shares: true,
      direct_grants: [],
      inherited_from_project: false,
      legacy_public_access: false,
    },
    isLoading: false,
    isError: false,
  }),
  useCreateShare: () => ({ mutate: mockCreateShare, isPending: false }),
  useUpdateShare: () => ({ mutate: mockUpdateShare, isPending: false }),
  useDeleteShare: () => ({ mutate: mockDeleteShare, isPending: false }),
}));

const renderDialog = () =>
  render(
    <ResourceShareDialog
      open
      onOpenChange={jest.fn()}
      resourceType="flow"
      resourceId="flow-1"
      resourceName="Quarterly agent"
    />,
  );

describe("ResourceShareDialog", () => {
  beforeEach(() => jest.clearAllMocks());

  it("offers exactly the two supported grant modes and creates a direct user grant", () => {
    renderDialog();

    expect(screen.getAllByText("Not editable — Can use")).toHaveLength(1);
    expect(screen.getAllByText("Editable — Can edit")).toHaveLength(1);
    expect(screen.queryByText(/public link/i)).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Second User" }));
    fireEvent.click(screen.getByRole("button", { name: "Share" }));

    expect(mockCreateShare).toHaveBeenCalledWith({
      resourceType: "flow",
      resourceId: "flow-1",
      recipientType: "user",
      recipientId: "user-2",
      permission: "execute",
    });
  });

  it("has no detectable axe violations in its ready state", async () => {
    renderDialog();

    expect(await axe(document.body)).toHaveNoViolations();
  });
});
