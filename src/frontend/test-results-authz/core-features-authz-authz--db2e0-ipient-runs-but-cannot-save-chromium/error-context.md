# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: core\features\authz\authz-team-sharing.spec.ts >> native team and resource sharing >> [AUTHZ-JOURNEY-02] ordinary owner shares a workflow as Can use and recipient runs but cannot save
- Location: tests\core\features\authz\authz-team-sharing.spec.ts:463:7

# Error details

```
Error: IBM accessibility regression detected: chromium__authz-read-only-flow-editor__1
Report: coverage/accessibility-reports/chromium__authz-read-only-flow-editor__1.html
New issues: 3
Report counts: violation=3, potential=63, recommendation=0, manual=1
Top issues (3/3 groups shown):
- [violation] aria_id_unique x1: The 'id' "node-Prompt, Template-3HRyE-field-template-label" specified for the ARIA property 'aria-labelledby' value is not valid
  xpath: /html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/main[1]/div[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]
  snippet: <div style="height: 40px; overflow-y: hidden;" data-placeholder="Type your prompt here..." class="relative min-h-10 overflow-y-auto rounded…
- [violation] input_label_exists x1: Form control with "textbox" role has no associated label
  xpath: /html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/main[1]/div[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]
  snippet: <div style="height: 40px; overflow-y: hidden;" data-placeholder="Type your prompt here..." class="relative min-h-10 overflow-y-auto rounded…
- [violation] aria_id_unique x1: The 'id' "node-Prompt, Template-3HRyE-field-input_value-label" specified for the ARIA property 'aria-labelledby' value is not valid
  xpath: /html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/main[1]/div[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[2]/div[2]/div[2]/div[2]/div[1]/div[1]/input[1]
  snippet: <input value="" type="text" aria-labelledby="node-Prompt Template-3HRyE-field-input_value-label" disabled="" data-testid="textarea_str_inpu…

expect(received).toBe(expected) // Object.is equality

Expected: 0
Received: 3
```

# Page snapshot

```yaml
- generic:
  - generic:
    - generic:
      - generic:
        - banner:
          - generic:
            - button:
              - img
          - generic:
            - generic:
              - generic:
                - generic:
                  - generic:
                    - button:
                      - generic: Owner bootstrap project 1788471248228-mfu629
                - generic: /
                - generic:
                  - img
                - button:
                  - generic: Runnable shared flow 1788471248228-mfu629
                  - img
          - generic:
            - generic:
              - generic:
                - button:
                  - generic: Go to GitHub repo
                  - generic:
                    - img
                    - generic: 154k
                - button:
                  - generic: Go to Discord server
                  - generic:
                    - img
                    - generic: 25k
            - button:
              - generic:
                - img
            - generic:
              - button:
                - generic:
                  - generic:
                    - generic:
                      - generic:
                        - img
                    - img
        - generic:
          - generic:
            - generic:
              - generic:
                - generic:
                  - generic:
                    - generic:
                      - navigation:
                        - generic:
                          - generic:
                            - generic:
                              - generic:
                                - list:
                                  - listitem:
                                    - button:
                                      - img
                                      - generic: Components
                                  - listitem:
                                    - button:
                                      - img
                                      - generic: MCP
                                  - listitem:
                                    - button:
                                      - img
                                      - generic: Bundles
                                  - listitem:
                                    - button:
                                      - img
                                      - generic: Versions
                                  - listitem
                                  - listitem:
                                    - button:
                                      - img
                                      - generic: Agent
                                  - listitem:
                                    - button:
                                      - img
                                      - generic: Memories
                                  - listitem:
                                    - button:
                                      - img
                                      - generic: Traces
                              - generic:
                                - generic:
                                  - generic:
                                    - generic:
                                      - img
                                      - searchbox
                                      - generic: Search
                                    - generic:
                                      - generic:
                                        - generic:
                                          - generic:
                                            - img:
                                              - generic:
                                                - generic: /
                                - generic:
                                  - generic:
                                    - generic:
                                      - generic: Components
                                      - generic:
                                        - button:
                                          - img
                                    - generic:
                                      - list:
                                        - listitem:
                                          - generic:
                                            - button:
                                              - img
                                              - generic: Input & Output
                                              - img
                                        - listitem:
                                          - generic:
                                            - button:
                                              - img
                                              - generic: Data Sources
                                              - img
                                        - listitem:
                                          - generic:
                                            - button:
                                              - img
                                              - generic: Models & Agents
                                              - img
                                        - listitem:
                                          - generic:
                                            - button:
                                              - img
                                              - generic: LLM Operations
                                              - img
                                        - listitem:
                                          - generic:
                                            - button:
                                              - img
                                              - generic: Files & Knowledge
                                              - img
                                        - listitem:
                                          - generic:
                                            - button:
                                              - img
                                              - generic: Processing
                                              - img
                                        - listitem:
                                          - generic:
                                            - button:
                                              - img
                                              - generic: Flow Control
                                              - img
                                        - listitem:
                                          - generic:
                                            - button:
                                              - img
                                              - generic: Utilities
                                              - img
                                        - listitem:
                                          - generic:
                                            - button:
                                              - img
                                              - generic: Prototypes
                                              - img
                                        - listitem:
                                          - generic:
                                            - button:
                                              - img
                                              - generic: Tools
                                              - img
                                  - button:
                                    - generic:
                                      - img
                                    - generic: Discover more components
                                - generic:
                                  - button:
                                    - img
                                    - generic: New Custom Component
                    - main:
                      - generic:
                        - generic:
                          - generic:
                            - generic:
                              - generic:
                                - button:
                                  - img
                                  - img
                              - button:
                                - generic:
                                  - generic: 100%
                                  - img
                              - button:
                                - img
                              - button:
                                - img
                              - button:
                                - img
                            - generic:
                              - generic:
                                - generic:
                                  - generic:
                                    - button [disabled]:
                                      - img
                                      - generic: Playground
                                  - button [expanded]:
                                    - text: Share
                                    - img
                            - application "Flow canvas":
                              - generic [ref=e1]:
                                - generic:
                                  - button [ref=e2] [cursor=pointer]
                                  - button [ref=e8] [cursor=pointer]
                                  - generic:
                                    - application [ref=e14]:
                                      - generic [ref=e16]:
                                        - generic [ref=e17]:
                                          - generic [ref=e18]:
                                            - generic [ref=e20]: Legacy
                                            - button [ref=e21] [cursor=pointer]: Dismiss
                                          - generic [ref=e23]:
                                            - text: Use
                                            - button [ref=e24] [cursor=pointer]: Chat Input
                                            - text: .
                                        - generic [ref=e25]:
                                          - generic [ref=e26]:
                                            - generic [ref=e27]:
                                              - img [ref=e29]
                                              - generic [ref=e34]:
                                                - generic [ref=e35]: Text Input
                                                - generic [ref=e37]: Legacy
                                            - generic [ref=e38]:
                                              - generic [ref=e42]: 52ms
                                              - button [ref=e44] [cursor=pointer]:
                                                - img [ref=e46]
                                          - paragraph [ref=e52]: Get user text inputs.
                                        - generic [ref=e53]:
                                          - generic [ref=e54]:
                                            - button [ref=e55]
                                            - generic [ref=e56]:
                                              - generic [ref=e58]:
                                                - generic [ref=e60]: Text
                                                - img [ref=e62]
                                              - generic [ref=e65]:
                                                - textbox [ref=e67]:
                                                  - /placeholder: Type something...
                                                  - text: owner seed
                                                - button [ref=e68] [cursor=pointer]:
                                                  - img [ref=e69]
                                          - generic [ref=e74]:
                                            - generic [ref=e76]:
                                              - generic [ref=e78]: Output Text
                                              - button [ref=e80] [cursor=pointer]:
                                                - img [ref=e81]
                                            - button [ref=e84]
                                    - application [ref=e85]:
                                      - generic [ref=e87]:
                                        - generic [ref=e88]:
                                          - generic [ref=e89]:
                                            - generic [ref=e90]:
                                              - img [ref=e92]
                                              - generic [ref=e99]: Prompt Template
                                            - generic [ref=e100]:
                                              - generic [ref=e104]: 39ms
                                              - button [ref=e106] [cursor=pointer]:
                                                - img [ref=e108]
                                          - paragraph [ref=e114]: Create a prompt template with dynamic variables.
                                        - generic [ref=e115]:
                                          - generic [ref=e117]:
                                            - generic [ref=e121]: Template
                                            - generic [ref=e124]:
                                              - generic [ref=e125]:
                                                - button [ref=e126] [cursor=pointer]:
                                                  - generic [ref=e127]: "{+}"
                                                - button [expanded] [ref=e128] [cursor=pointer]:
                                                  - img [ref=e129]
                                              - generic [ref=e133]:
                                                - textbox [ref=e134]
                                                - button [ref=e136] [cursor=pointer]:
                                                  - img
                                          - generic [ref=e137]:
                                            - button [ref=e138]
                                            - generic [ref=e139]:
                                              - generic [ref=e143]: input_value
                                              - generic [ref=e144]:
                                                - generic:
                                                  - generic:
                                                    - textbox [disabled]:
                                                      - /placeholder: Receiving input
                                                    - generic: Receiving input
                                                  - button [disabled]:
                                                    - img
                                          - generic [ref=e145]:
                                            - generic [ref=e147]:
                                              - generic [ref=e149]: Prompt
                                              - button [ref=e151] [cursor=pointer]:
                                                - img [ref=e152]
                                            - button [ref=e155]
                                    - application [ref=e156]:
                                      - generic [ref=e158]:
                                        - generic [ref=e161]:
                                          - button [ref=e162] [cursor=pointer]:
                                            - img
                                            - generic [ref=e163]: Code
                                          - button [ref=e164] [cursor=pointer]:
                                            - img
                                            - generic [ref=e165]: Parameters
                                          - button [ref=e166] [cursor=pointer]:
                                            - img
                                            - generic [ref=e167]: Freeze
                                          - combobox [ref=e168] [cursor=pointer]:
                                            - img [ref=e170]
                                        - button [ref=e174] [cursor=pointer]:
                                          - img [ref=e175]
                                        - generic [ref=e178]:
                                          - generic [ref=e179]:
                                            - generic [ref=e181]: Legacy
                                            - button [ref=e182] [cursor=pointer]: Dismiss
                                          - generic [ref=e184]:
                                            - text: Use
                                            - button [ref=e185] [cursor=pointer]: Chat Output
                                            - text: .
                                        - generic [ref=e186]:
                                          - generic [ref=e187]:
                                            - generic [ref=e188]:
                                              - img [ref=e190]
                                              - generic [ref=e195]:
                                                - generic [ref=e196]: Text Output
                                                - generic [ref=e198]: Legacy
                                            - generic [ref=e199]:
                                              - generic [ref=e203]: 6ms
                                              - button [ref=e205] [cursor=pointer]:
                                                - img [ref=e207]
                                          - paragraph [ref=e213]: Sends text output via API.
                                        - generic [ref=e214]:
                                          - generic [ref=e215]:
                                            - button [ref=e216]
                                            - generic [ref=e217]:
                                              - generic [ref=e219]:
                                                - generic [ref=e221]: Inputs
                                                - img [ref=e223]
                                              - generic [ref=e225]:
                                                - generic:
                                                  - generic:
                                                    - textbox [disabled]:
                                                      - /placeholder: Receiving input
                                                    - generic: Receiving input
                                                  - button [disabled]:
                                                    - img
                                          - generic [ref=e226]:
                                            - generic [ref=e228]:
                                              - generic [ref=e230]: Output Text
                                              - button [ref=e232] [cursor=pointer]:
                                                - img [ref=e233]
                                            - button [ref=e236]
                              - generic:
                                - img
      - generic:
        - region "Notifications":
          - status
  - generic:
    - menu:
      - menuitem:
        - img
        - text: Share
      - menuitem:
        - img
        - generic: API access
      - menuitem:
        - img
        - generic: Export
      - link:
        - /url: /mcp/folder/86fca492-697b-4497-abef-9356a3d7c776
        - menuitem:
          - img
          - generic: MCP Server
      - menuitem:
        - img
        - generic: Embed into site
      - menuitem [disabled]:
        - generic:
          - generic:
            - generic:
              - img
              - generic: Shareable Playground
          - switch [disabled]
  - dialog "Share “Runnable shared flow 1788471248228-mfu629”" [active] [ref=e238]:
    - generic [ref=e239]:
      - heading "Share “Runnable shared flow 1788471248228-mfu629”" [level=2] [ref=e240]
      - paragraph [ref=e241]: Choose who can access this resource and what they can do.
    - region "Add access" [ref=e242]:
      - heading "Add access" [level=3] [ref=e243]
      - radiogroup "Recipient type" [ref=e244]:
        - generic [ref=e245] [cursor=pointer]:
          - radio "User" [checked] [ref=e246]:
            - img [ref=e247]
          - text: User
        - generic [ref=e249] [cursor=pointer]:
          - radio "Team" [ref=e250]
          - text: Team
      - generic [ref=e251]:
        - text: Search recipients
        - generic [ref=e252]:
          - textbox "Search recipients" [ref=e253]:
            - /placeholder: Search for a user
          - generic: Search for a user
        - paragraph [ref=e254]: Enter at least two characters. Only eligible recipients are shown.
      - radiogroup "Access level" [ref=e255]:
        - generic [ref=e256] [cursor=pointer]:
          - radio "Not editable — Can use Can view and run. Cannot change this resource." [checked] [ref=e257]:
            - img [ref=e258]
          - generic [ref=e260]:
            - generic [ref=e261]: Not editable — Can use
            - generic [ref=e262]: Can view and run. Cannot change this resource.
        - generic [ref=e263] [cursor=pointer]:
          - radio "Editable — Can edit Can view, run, and edit. Cannot reshare or delete it." [ref=e264]
          - generic [ref=e265]:
            - generic [ref=e266]: Editable — Can edit
            - generic [ref=e267]: Can view, run, and edit. Cannot reshare or delete it.
      - button "Share" [disabled]
    - region "People and teams with access" [ref=e268]:
      - heading "People and teams with access" [level=3] [ref=e269]
      - list [ref=e270]:
        - listitem [ref=e271]:
          - generic [ref=e272]:
            - generic [ref=e273]:
              - generic [ref=e274]: authz-direct-1788471248228-mfu629
              - generic [ref=e275]: User
            - button "Remove access for authz-direct-1788471248228-mfu629" [ref=e276] [cursor=pointer]: Remove
          - radiogroup "Permission for authz-direct-1788471248228-mfu629" [ref=e277]:
            - generic [ref=e278] [cursor=pointer]:
              - radio "Not editable — Can use" [checked] [ref=e279]:
                - img [ref=e280]
              - generic [ref=e282]: Not editable — Can use
            - generic [ref=e283] [cursor=pointer]:
              - radio "Editable — Can edit" [ref=e284]
              - generic [ref=e285]: Editable — Can edit
      - alert [ref=e286]:
        - generic [ref=e287]: Removing one grant may not remove access supplied by another source.
    - button "Close" [ref=e289] [cursor=pointer]
    - button "Close" [ref=e290] [cursor=pointer]:
      - img [ref=e291]
      - generic [ref=e293]: Close
```

# Test source

```ts
  124 | 
  125 |     const errors: Array<{
  126 |       path: string;
  127 |       status: number;
  128 |       statusText: string;
  129 |       responseBody?: string;
  130 |       type?: string;
  131 |     }> = [];
  132 |     const clientErrors: ObservedHttpError[] = [];
  133 |     const serverErrorContract = createServerErrorContract();
  134 |     const pendingApiResponseStatuses = createPendingRequestTracker<Request>();
  135 |     const pendingApiRequestLifecycles = createPendingRequestTracker<Request>();
  136 |     const pendingResponseInspections = new Set<Promise<void>>();
  137 |     const responseInspectionErrors: Error[] = [];
  138 | 
  139 |     // Flag to allow flow errors (for tests that expect errors)
  140 |     let allowFlowErrors = false;
  141 | 
  142 |     // Add helper method to page context — see LangflowPage type in utils/types.ts
  143 |     (page as Page & { allowFlowErrors?: () => void }).allowFlowErrors = () => {
  144 |       allowFlowErrors = true;
  145 |     };
  146 |     (
  147 |       page as Page & {
  148 |         expectServerError?: (expectation: ExpectedServerError) => void;
  149 |       }
  150 |     ).expectServerError = (expectation) => {
  151 |       expectServerError(serverErrorContract, expectation);
  152 |     };
  153 |     const allowedPendingRequests: AllowedPendingRequest[] = [];
  154 |     (
  155 |       page as Page & {
  156 |         expectPendingRequest?: (expectation: AllowedPendingRequest) => void;
  157 |       }
  158 |     ).expectPendingRequest = (expectation) => {
  159 |       allowedPendingRequests.push(expectation);
  160 |     };
  161 | 
  162 |     let a11yScanIndex = 0;
  163 |     (
  164 |       page as Page & {
  165 |         runA11yScan?: (
  166 |           label: string,
  167 |           options?: A11yScanOptions,
  168 |         ) => Promise<ICheckerResult | null>;
  169 |       }
  170 |     ).runA11yScan = async (label: string, options?: A11yScanOptions) => {
  171 |       if (!RUN_A11Y) {
  172 |         return null;
  173 |       }
  174 | 
  175 |       if (options?.colorScheme) {
  176 |         await page.emulateMedia({ colorScheme: options.colorScheme });
  177 |       }
  178 | 
  179 |       // Let enter animations (Radix popover/dialog fade-ins) finish before
  180 |       // scanning. The IBM checker composites element opacity into its
  181 |       // contrast measurement, so a popover caught mid `fade-in` reports
  182 |       // phantom text_contrast_sufficient violations (LE-2235: 4.00:1 on
  183 |       // the model picker that measures 4.95:1 once settled). Infinite
  184 |       // animations (spinners) are skipped; the 2s cap keeps a stuck
  185 |       // animation from hanging the scan.
  186 |       await page.evaluate(() =>
  187 |         Promise.race([
  188 |           Promise.all(
  189 |             document
  190 |               .getAnimations()
  191 |               .filter((a) => {
  192 |                 const timing = a.effect?.getTiming();
  193 |                 return timing?.iterations !== Infinity;
  194 |               })
  195 |               .map((a) => a.finished.catch(() => undefined)),
  196 |           ),
  197 |           new Promise((resolve) => setTimeout(resolve, 2000)),
  198 |         ]),
  199 |       );
  200 | 
  201 |       const scanIndex = a11yScanIndex++;
  202 |       const scanLabel = buildA11yScanLabel(
  203 |         testInfo.project.name,
  204 |         label,
  205 |         scanIndex,
  206 |       );
  207 | 
  208 |       const result = await aChecker.getCompliance(page, scanLabel);
  209 | 
  210 |       if (!isCheckerReport(result.report)) {
  211 |         throw new Error(
  212 |           `IBM accessibility scan failed for ${scanLabel}: checker returned an error payload.`,
  213 |         );
  214 |       }
  215 | 
  216 |       testInfo.attachments.push(
  217 |         buildA11ySummaryAttachment(scanIndex, scanLabel, result.report),
  218 |       );
  219 | 
  220 |       if (RUN_A11Y_ASSERT) {
  221 |         const newViolationCount = countNewA11yViolations(result.report);
  222 |         const failureMessage = formatA11yFailure(scanLabel, result.report);
  223 | 
> 224 |         expect(newViolationCount, failureMessage).toBe(0);
      |                                                   ^ Error: IBM accessibility regression detected: chromium__authz-read-only-flow-editor__1
  225 |       }
  226 | 
  227 |       return result;
  228 |     };
  229 | 
  230 |     // Monitor API responses for errors
  231 |     const inspectResponse = async (response: Response) => {
  232 |       const url = response.url();
  233 |       const status = response.status();
  234 | 
  235 |       if (url.includes("/api/") && status >= 400) {
  236 |         const method = response.request().method().toUpperCase();
  237 |         const path = new URL(url).pathname;
  238 |         const observed: ObservedHttpError = {
  239 |           method,
  240 |           path,
  241 |           status,
  242 |           statusText: response.statusText(),
  243 |           responseBody: await getResponseBody(response, `${method} ${path}`),
  244 |         };
  245 | 
  246 |         if (status < 500) {
  247 |           if (clientErrors.length < MAX_CLIENT_ERROR_DIAGNOSTICS) {
  248 |             clientErrors.push(observed);
  249 |           }
  250 |         } else {
  251 |           observeServerError(serverErrorContract, observed);
  252 |         }
  253 |       }
  254 | 
  255 |       // Monitor event delivery endpoints for error messages (streaming/polling/direct)
  256 |       if (
  257 |         status === 200 &&
  258 |         (url.includes("/events?event_delivery=") ||
  259 |           url.includes("/build/") ||
  260 |           url.includes("/run/"))
  261 |       ) {
  262 |         try {
  263 |           const headers = response.headers();
  264 |           const contentType = (headers["content-type"] || "").toLowerCase();
  265 |           const streamingContentHints = [
  266 |             "text/event-stream",
  267 |             "application/grpc",
  268 |             "application/octet-stream",
  269 |             "application/x-ndjson",
  270 |           ];
  271 |           const isStreamLike = streamingContentHints.some((hint) =>
  272 |             contentType.includes(hint),
  273 |           );
  274 |           if (isStreamLike) {
  275 |             return;
  276 |           }
  277 | 
  278 |           const method = response.request().method().toUpperCase();
  279 |           const path = new URL(url).pathname;
  280 |           const bodyResult = await readResponseBodyWithTimeout(response, {
  281 |             timeoutMs: RESPONSE_BODY_READ_TIMEOUT_MS,
  282 |             label: `${method} ${path}`,
  283 |           });
  284 |           if (bodyResult.status !== "success") {
  285 |             console.warn(`${bodyResult.diagnostic} Skipping body inspection.`);
  286 |             return;
  287 |           }
  288 |           const responseBody = bodyResult.body;
  289 |           if (!responseBody) {
  290 |             return;
  291 |           }
  292 | 
  293 |           // Try to parse as JSON and extract error details
  294 |           let errorPreview: string | null = null;
  295 |           let hasError = false;
  296 | 
  297 |           try {
  298 |             const lines = responseBody.split("\n");
  299 |             for (const line of lines) {
  300 |               if (line.trim()) {
  301 |                 try {
  302 |                   const json = JSON.parse(line);
  303 | 
  304 |                   // Check for error in params field (build errors)
  305 |                   if (json.data?.build_data?.params?.startsWith("Error")) {
  306 |                     errorPreview = json.data.build_data.params;
  307 |                     hasError = true;
  308 |                     break;
  309 |                   }
  310 | 
  311 |                   // Check for error: true (not error: false)
  312 |                   if (json.data?.error === true || json.error === true) {
  313 |                     const errMsg =
  314 |                       json.data?.error_message ||
  315 |                       json.error_message ||
  316 |                       "Unknown error";
  317 |                     errorPreview = errMsg;
  318 |                     hasError = true;
  319 |                     break;
  320 |                   }
  321 |                 } catch (_lineParseErr) {
  322 |                   // Skip lines that aren't valid JSON
  323 |                 }
  324 |               }
```