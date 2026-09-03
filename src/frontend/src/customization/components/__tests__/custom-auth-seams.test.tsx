import { fireEvent, render, screen } from "@testing-library/react";
import type { AxiosError } from "axios";
import { customShouldSkipAuthRefresh } from "../../utils/custom-should-skip-auth-refresh";
import { CustomAdminPageMenuItem } from "../custom-admin-page-menu-item";
import { CustomHeaderMenuItemsTitle } from "../custom-header-menu-items-title";
import CustomLoginBrandTitle from "../custom-login-brand-title";
import CustomLoginSignupPrompt from "../custom-login-signup-prompt";
import CustomLoginSsoOptions from "../custom-login-sso-options";
import CustomResourceShareAction from "../custom-resource-share-action";
import CustomSettingsPasswordFormGate from "../custom-settings-password-form-gate";

const mockCapabilities = jest.fn();
const mockPermissions = jest.fn();

jest.mock("@/controllers/API/queries/authorization", () => ({
  useGetAuthorizationCapabilities: () => mockCapabilities(),
}));

jest.mock("@/contexts/permissionsContext", () => ({
  usePermissions: () => mockPermissions(),
}));

jest.mock("@/components/core/appHeaderComponent/components/HeaderMenu", () => ({
  HeaderMenuItemButton: ({
    children,
    onClick,
  }: {
    children: React.ReactNode;
    onClick: () => void;
  }) => (
    <button type="button" onClick={onClick}>
      {children}
    </button>
  ),
}));

jest.mock("../resource-share-dialog", () => () => null);

describe("OSS auth customization seams", () => {
  beforeEach(() => {
    mockCapabilities.mockReturnValue({
      data: { enforcement_active: false, service_ready: false },
      isLoading: false,
      isError: false,
    });
    mockPermissions.mockReturnValue({
      capability: jest.fn(() => false),
      isUnavailable: true,
    });
  });

  it("does not render collaboration navigation when the server contract is unavailable", () => {
    const { container } = render(
      <CustomAdminPageMenuItem onNavigate={jest.fn()} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("renders member navigation only after the server reports readiness", () => {
    const onNavigate = jest.fn();
    mockCapabilities.mockReturnValue({
      data: {
        enforcement_active: true,
        service_ready: true,
        can_administer_platform: false,
      },
      isLoading: false,
      isError: false,
    });

    render(<CustomAdminPageMenuItem onNavigate={onNavigate} />);

    fireEvent.click(screen.getByTestId("menu-teams-button"));
    expect(onNavigate).toHaveBeenCalledWith("/teams");
    expect(screen.getByTestId("menu-shared-with-me-button")).toBeVisible();
    expect(screen.queryByTestId("menu-admin-teams-button")).toBeNull();
  });

  it("adds the platform Teams destination only for a Platform Admin", () => {
    mockCapabilities.mockReturnValue({
      data: {
        enforcement_active: true,
        service_ready: true,
        can_administer_platform: true,
      },
      isLoading: false,
      isError: false,
    });

    render(<CustomAdminPageMenuItem onNavigate={jest.fn()} />);

    expect(screen.getByTestId("menu-admin-teams-button")).toBeVisible();
  });

  it("does not render an account-menu identity header", () => {
    const { container } = render(<CustomHeaderMenuItemsTitle />);

    expect(container).toBeEmptyDOMElement();
  });

  it("renders the OSS product name as the login brand", () => {
    render(<CustomLoginBrandTitle />);

    expect(screen.getByText("Langflow")).toBeInTheDocument();
  });

  it("passes signup prompt children through", () => {
    render(
      <CustomLoginSignupPrompt>
        <p>Don't have an account? Sign Up</p>
      </CustomLoginSignupPrompt>,
    );

    expect(
      screen.getByText("Don't have an account? Sign Up"),
    ).toBeInTheDocument();
  });

  it("passes the settings password form through", () => {
    render(
      <CustomSettingsPasswordFormGate>
        <p>Password settings</p>
      </CustomSettingsPasswordFormGate>,
    );

    expect(screen.getByText("Password settings")).toBeInTheDocument();
  });

  it("renders no SSO login options", () => {
    const { container } = render(<CustomLoginSsoOptions />);

    expect(container).toBeEmptyDOMElement();
  });

  it("keeps project sharing inert until server and resource capabilities agree", () => {
    const { container } = render(
      <CustomResourceShareAction
        resourceId="resource-1"
        resourceType="project"
        resourceName="Project one"
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("renders project Share for an authorized owner", () => {
    mockCapabilities.mockReturnValue({
      data: {
        enforcement_active: true,
        service_ready: true,
        user_team_sharing_supported: true,
      },
      isLoading: false,
      isError: false,
    });
    mockPermissions.mockReturnValue({
      capability: jest.fn(() => true),
      isUnavailable: false,
    });

    render(
      <CustomResourceShareAction
        resourceId="resource-1"
        resourceType="project"
        resourceName="Project one"
        display="label"
      />,
    );

    expect(
      screen.getByRole("button", { name: /Share Project one/i }),
    ).toBeVisible();
  });

  it("never skips auth refresh", () => {
    const error = {
      response: { status: 403, data: { detail: "must_change_password" } },
    } as AxiosError;

    expect(customShouldSkipAuthRefresh(error)).toBe(false);
  });
});
