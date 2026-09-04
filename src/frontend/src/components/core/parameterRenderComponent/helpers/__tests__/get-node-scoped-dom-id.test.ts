import { getDomId, getNodeScopedDomId } from "../get-node-scoped-dom-id";

describe("DOM id helpers", () => {
  it("encodes every dynamic segment for ARIA IDREF safety", () => {
    const id = getDomId(
      "node",
      "Prompt, Template-B8Bz7",
      "field",
      "input value",
      "label",
    );

    expect(id).toBe(
      "node-Prompt%2C%20Template-B8Bz7-field-input%20value-label",
    );
    expect(id).not.toMatch(/\s/);
  });

  it("keeps the existing base id while safely scoping it to a node", () => {
    expect(
      getNodeScopedDomId(
        "promptarea_prompt_template",
        "Prompt, Template-B8Bz7",
      ),
    ).toBe("promptarea_prompt_template-Prompt%2C%20Template-B8Bz7");
  });

  it("preserves an absent id", () => {
    expect(getNodeScopedDomId()).toBeUndefined();
  });
});
