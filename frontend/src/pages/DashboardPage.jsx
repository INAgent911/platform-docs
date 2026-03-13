import {
  Alert,
  AppBar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  FormControl,
  Grid,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Select,
  Stack,
  Tab,
  Tabs,
  TextField,
  Toolbar,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth/AuthContext";

const defaultSchemaYaml = `entity_name: ticket
version: 1
strategy: typed
fields:
  - name: client_reference
    type: string
    required: false
    description: External customer reference
    vectorize: false
`;

const fmt = (value) => (value ? new Date(value).toLocaleString() : "n/a");

const CardSection = ({ title, children }) => (
  <Card>
    <CardContent>
      <Typography variant="h6">{title}</Typography>
      <Box mt={2}>{children}</Box>
    </CardContent>
  </Card>
);

export default function DashboardPage() {
  const { me, logout } = useAuth();
  const isAdminSurface = useMemo(() => me?.role === "owner" || me?.role === "admin", [me]);
  const [tab, setTab] = useState("overview");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [tenant, setTenant] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [changes, setChanges] = useState([]);
  const [runbooks, setRunbooks] = useState([]);
  const [users, setUsers] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [manifests, setManifests] = useState([]);
  const [customerName, setCustomerName] = useState("");
  const [ticketTitle, setTicketTitle] = useState("");
  const [incidentTitle, setIncidentTitle] = useState("");
  const [incidentSeverity, setIncidentSeverity] = useState("sev3");
  const [changeTitle, setChangeTitle] = useState("");
  const [changeType, setChangeType] = useState("normal");
  const [changeRisk, setChangeRisk] = useState(5);
  const [changeRollback, setChangeRollback] = useState("");
  const [changeRunbookId, setChangeRunbookId] = useState("");
  const [runbookName, setRunbookName] = useState("");
  const [runbookAuto, setRunbookAuto] = useState("no");
  const [provisioningJobs, setProvisioningJobs] = useState([]);
  const [workflowTemplates, setWorkflowTemplates] = useState([]);
  const [opsReport, setOpsReport] = useState(null);
  const [usageReport, setUsageReport] = useState(null);
  const [aiQuery, setAiQuery] = useState("email outage authentication errors");
  const [aiResult, setAiResult] = useState(null);
  const [uiThemeMode, setUiThemeMode] = useState("light");
  const [uiPrimaryColor, setUiPrimaryColor] = useState("#0b5fff");
  const [schemaYaml, setSchemaYaml] = useState(defaultSchemaYaml);
  const [schemaResult, setSchemaResult] = useState("");
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserRole, setNewUserRole] = useState("user");

  const fail = (err) => {
    setNotice("");
    const detail = err?.response?.data?.detail;
    setError(typeof detail === "string" ? detail : "Request failed");
  };
  const ok = (msg) => {
    setError("");
    setNotice(msg);
  };

  useEffect(() => {
    if (changeType !== "standard") setChangeRunbookId("");
  }, [changeType]);

  const loadData = async () => {
    const [tenantResp, customerResp, ticketResp, incidentResp, changeResp] = await Promise.all([
      api.get("/tenants/me"),
      api.get("/customers"),
      api.get("/tickets"),
      api.get("/incidents"),
      api.get("/changes"),
    ]);
    setTenant(tenantResp.data);
    setCustomers(customerResp.data);
    setTickets(ticketResp.data);
    setIncidents(incidentResp.data);
    setChanges(changeResp.data);
    try {
      const runbookResp = await api.get("/runbooks");
      setRunbooks(runbookResp.data);
    } catch {
      setRunbooks([]);
    }
    if (isAdminSurface) {
      const [usersResp, permsResp, manifestsResp] = await Promise.all([
        api.get("/rbac/users"),
        api.get("/rbac/permissions"),
        api.get("/schema/manifests"),
      ]);
      setUsers(usersResp.data);
      setPermissions(permsResp.data);
      setManifests(manifestsResp.data);
      try {
        const [provResp, templateResp, opsResp, usageResp, uiResp] = await Promise.all([
          api.get("/provisioning"),
          api.get("/workflows/templates"),
          api.get("/reports/operations"),
          api.get("/reports/usage"),
          api.get("/ui/settings"),
        ]);
        setProvisioningJobs(provResp.data);
        setWorkflowTemplates(templateResp.data);
        setOpsReport(opsResp.data);
        setUsageReport(usageResp.data);
        setUiThemeMode(uiResp.data.theme_mode);
        setUiPrimaryColor(uiResp.data.primary_color);
      } catch {
        setProvisioningJobs([]);
        setWorkflowTemplates([]);
      }
    }
  };

  useEffect(() => {
    loadData().catch(fail);
  }, [isAdminSurface]);

  const createCustomer = async (event) => {
    event.preventDefault();
    try {
      await api.post("/customers", { name: customerName, status: "active" });
      setCustomerName("");
      ok("Customer created");
      await loadData();
    } catch (err) {
      fail(err);
    }
  };

  const createTicket = async (event) => {
    event.preventDefault();
    try {
      await api.post("/tickets", { title: ticketTitle, priority: "p3" });
      setTicketTitle("");
      ok("Ticket created");
      await loadData();
    } catch (err) {
      fail(err);
    }
  };

  const createIncident = async (event) => {
    event.preventDefault();
    try {
      await api.post("/incidents", { title: incidentTitle, severity: incidentSeverity, status: "open" });
      setIncidentTitle("");
      ok("Incident created");
      await loadData();
    } catch (err) {
      fail(err);
    }
  };

  const createChange = async (event) => {
    event.preventDefault();
    try {
      const payload = {
        title: changeTitle,
        change_type: changeType,
        risk_score: Number(changeRisk),
        rollback_plan: changeRollback || null,
      };
      if (changeType === "standard" && changeRunbookId) payload.runbook_id = changeRunbookId;
      await api.post("/changes", payload);
      setChangeTitle("");
      ok("Change created");
      await loadData();
    } catch (err) {
      fail(err);
    }
  };

  const createRunbook = async (event) => {
    event.preventDefault();
    try {
      await api.post("/runbooks", {
        name: runbookName,
        auto_approve_low_risk: runbookAuto === "yes",
        min_risk_score: 1,
        max_risk_score: 3,
      });
      setRunbookName("");
      setRunbookAuto("no");
      ok("Runbook created");
      await loadData();
    } catch (err) {
      fail(err);
    }
  };

  const changeAction = async (changeId, action, body = null, msg = "Change updated") => {
    try {
      await api.post(`/changes/${changeId}/${action}`, body);
      ok(msg);
      await loadData();
    } catch (err) {
      fail(err);
    }
  };

  const incidentComms = async (incidentId) => {
    try {
      await api.post(`/incidents/${incidentId}/communications`, { note: "Customer update sent" });
      ok("Communication logged");
      await loadData();
    } catch (err) {
      fail(err);
    }
  };

  const createUser = async (event) => {
    event.preventDefault();
    try {
      await api.post("/rbac/users", {
        email: newUserEmail,
        first_name: "New",
        last_name: "User",
        password: "ChangeMe123!",
        role: newUserRole,
      });
      setNewUserEmail("");
      ok("User created");
      await loadData();
    } catch (err) {
      fail(err);
    }
  };

  const runSchema = async (apply) => {
    try {
      const path = apply ? "/schema/apply-yaml" : "/schema/plan-yaml";
      const response = await api.post(path, { content: schemaYaml });
      setSchemaResult(JSON.stringify(response.data, null, 2));
      ok(apply ? "Schema applied" : "Schema planned");
      if (apply) await loadData();
    } catch (err) {
      fail(err);
    }
  };

  return (
    <Box>
      <AppBar position="static">
        <Toolbar sx={{ gap: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>MSP Platform</Typography>
          <Chip label={`${me?.first_name} ${me?.last_name} (${me?.role})`} variant="outlined" sx={{ color: "white", borderColor: "white" }} />
          <Button color="inherit" onClick={logout}>Sign Out</Button>
        </Toolbar>
      </AppBar>

      <Container sx={{ py: 3 }}>
        <Stack spacing={2}>
          <Typography variant="h5" fontWeight={700}>{tenant?.name || "Tenant"}</Typography>
          {notice && <Alert severity="success">{notice}</Alert>}
          {error && <Alert severity="error">{error}</Alert>}

          <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable">
            <Tab value="overview" label="Overview" />
            <Tab value="operations" label="Operations" />
            {isAdminSurface && <Tab value="schema" label="Schema" />}
            {isAdminSurface && <Tab value="rbac" label="RBAC" />}
          </Tabs>

          {tab === "overview" && (
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <CardSection title={`Customers (${customers.length})`}>
                  <Box component="form" onSubmit={createCustomer}>
                    <Stack spacing={1}>
                      <TextField label="Customer Name" value={customerName} onChange={(e) => setCustomerName(e.target.value)} />
                      <Button type="submit" variant="contained">Add Customer</Button>
                    </Stack>
                  </Box>
                </CardSection>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <CardSection title={`Tickets (${tickets.length})`}>
                  <Box component="form" onSubmit={createTicket}>
                    <Stack spacing={1}>
                      <TextField label="Ticket Title" value={ticketTitle} onChange={(e) => setTicketTitle(e.target.value)} />
                      <Button type="submit" variant="contained">Add Ticket</Button>
                    </Stack>
                  </Box>
                  <List dense>
                    {tickets.slice(0, 6).map((ticket) => (
                      <ListItem key={ticket.id} divider>
                        <ListItemText
                          primary={`${ticket.title} (${ticket.priority})`}
                          secondary={`response due ${fmt(ticket.response_due_at)} | resolve due ${fmt(ticket.resolve_due_at)}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardSection>
              </Grid>
            </Grid>
          )}

          {tab === "operations" && (
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 4 }}>
                <CardSection title={`Incidents (${incidents.length})`}>
                  <Box component="form" onSubmit={createIncident}>
                    <Stack spacing={1}>
                      <TextField label="Title" value={incidentTitle} onChange={(e) => setIncidentTitle(e.target.value)} />
                      <FormControl fullWidth>
                        <InputLabel id="sev-label">Severity</InputLabel>
                        <Select labelId="sev-label" value={incidentSeverity} label="Severity" onChange={(e) => setIncidentSeverity(e.target.value)}>
                          <MenuItem value="sev1">SEV1</MenuItem>
                          <MenuItem value="sev2">SEV2</MenuItem>
                          <MenuItem value="sev3">SEV3</MenuItem>
                          <MenuItem value="sev4">SEV4</MenuItem>
                        </Select>
                      </FormControl>
                      <Button type="submit" variant="contained">Create Incident</Button>
                    </Stack>
                  </Box>
                  <List dense>
                    {incidents.slice(0, 5).map((incident) => (
                      <ListItem key={incident.id} divider>
                        <Stack sx={{ width: "100%" }} spacing={0.5}>
                          <ListItemText primary={incident.title} secondary={`${incident.status} | next comm ${fmt(incident.next_communication_due_at)}`} />
                          <Button size="small" variant="outlined" onClick={() => incidentComms(incident.id)}>Log Comms</Button>
                        </Stack>
                      </ListItem>
                    ))}
                  </List>
                </CardSection>
              </Grid>

              <Grid size={{ xs: 12, md: 4 }}>
                <CardSection title={`Changes (${changes.length})`}>
                  <Box component="form" onSubmit={createChange}>
                    <Stack spacing={1}>
                      <TextField label="Title" value={changeTitle} onChange={(e) => setChangeTitle(e.target.value)} />
                      <FormControl fullWidth>
                        <InputLabel id="type-label">Type</InputLabel>
                        <Select labelId="type-label" value={changeType} label="Type" onChange={(e) => setChangeType(e.target.value)}>
                          <MenuItem value="standard">Standard</MenuItem>
                          <MenuItem value="normal">Normal</MenuItem>
                          <MenuItem value="emergency">Emergency</MenuItem>
                        </Select>
                      </FormControl>
                      <TextField label="Risk (1-10)" type="number" value={changeRisk} onChange={(e) => setChangeRisk(e.target.value)} />
                      {changeType === "standard" && (
                        <FormControl fullWidth>
                          <InputLabel id="runbook-label">Runbook</InputLabel>
                          <Select labelId="runbook-label" value={changeRunbookId} label="Runbook" onChange={(e) => setChangeRunbookId(e.target.value)}>
                            {runbooks.map((r) => (
                              <MenuItem key={r.id} value={r.id}>{r.name}</MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      )}
                      <TextField label="Rollback Plan" value={changeRollback} onChange={(e) => setChangeRollback(e.target.value)} />
                      <Button type="submit" variant="contained">Create Change</Button>
                    </Stack>
                  </Box>
                  <List dense>
                    {changes.slice(0, 6).map((change) => (
                      <ListItem key={change.id} divider>
                        <Stack spacing={0.5} sx={{ width: "100%" }}>
                          <ListItemText primary={change.title} secondary={`${change.status} | ${change.change_type} | execution ${change.execution_status}`} />
                          <Stack direction="row" spacing={1}>
                            {(change.status === "draft" || change.status === "rejected") && (
                              <Button size="small" onClick={() => changeAction(change.id, "submit-approval", null, "Submitted")}>Submit</Button>
                            )}
                            {change.status === "pending_approval" && (
                              <Button size="small" onClick={() => changeAction(change.id, "approval", { approved: true, approval_notes: "Approved" }, "Approved")}>Approve</Button>
                            )}
                            {change.status === "approved" && change.change_type === "standard" && change.runbook_id && (
                              <Button size="small" onClick={() => changeAction(change.id, "execute-runbook", null, "Runbook executed")}>Execute</Button>
                            )}
                            {change.status === "approved" && (
                              <Button size="small" onClick={() => changeAction(change.id, "start", null, "Started")}>Start</Button>
                            )}
                            {change.status === "in_progress" && (
                              <Button size="small" onClick={() => changeAction(change.id, "complete", { rolled_back: false }, "Completed")}>Complete</Button>
                            )}
                          </Stack>
                        </Stack>
                      </ListItem>
                    ))}
                  </List>
                </CardSection>
              </Grid>

              <Grid size={{ xs: 12, md: 4 }}>
                <CardSection title={`Runbooks (${runbooks.length})`}>
                  {isAdminSurface && (
                    <Box component="form" onSubmit={createRunbook}>
                      <Stack spacing={1}>
                        <TextField label="Runbook Name" value={runbookName} onChange={(e) => setRunbookName(e.target.value)} />
                        <FormControl fullWidth>
                          <InputLabel id="auto-label">Auto-Approve</InputLabel>
                          <Select labelId="auto-label" value={runbookAuto} label="Auto-Approve" onChange={(e) => setRunbookAuto(e.target.value)}>
                            <MenuItem value="no">No</MenuItem>
                            <MenuItem value="yes">Yes</MenuItem>
                          </Select>
                        </FormControl>
                        <Button type="submit" variant="contained">Create Runbook</Button>
                      </Stack>
                    </Box>
                  )}
                  <List dense>
                    {runbooks.map((runbook) => (
                      <ListItem key={runbook.id} divider>
                        <ListItemText primary={runbook.name} secondary={`auto-approve ${runbook.auto_approve_low_risk ? "yes" : "no"}`} />
                      </ListItem>
                    ))}
                  </List>
                </CardSection>
              </Grid>
            </Grid>
          )}

          {tab === "schema" && (
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 8 }}>
                <CardSection title="Schema Controller">
                  <Stack spacing={1}>
                    <TextField multiline minRows={10} value={schemaYaml} onChange={(e) => setSchemaYaml(e.target.value)} />
                    <Stack direction="row" spacing={1}>
                      <Button variant="outlined" onClick={() => runSchema(false)}>Plan</Button>
                      <Button variant="contained" onClick={() => runSchema(true)}>Apply</Button>
                    </Stack>
                    <TextField multiline minRows={8} value={schemaResult} InputProps={{ readOnly: true }} />
                  </Stack>
                </CardSection>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <CardSection title={`Manifests (${manifests.length})`}>
                  <List dense>
                    {manifests.map((m) => (
                      <ListItem key={m.id} divider>
                        <ListItemText primary={`${m.entity_name} v${m.version}`} secondary={`${m.strategy} | ${m.status}`} />
                      </ListItem>
                    ))}
                  </List>
                </CardSection>
              </Grid>
            </Grid>
          )}

          {tab === "rbac" && (
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <CardSection title="Create User">
                  <Box component="form" onSubmit={createUser}>
                    <Stack spacing={1}>
                      <TextField label="Email" value={newUserEmail} onChange={(e) => setNewUserEmail(e.target.value)} />
                      <FormControl fullWidth>
                        <InputLabel id="role-label">Role</InputLabel>
                        <Select labelId="role-label" value={newUserRole} label="Role" onChange={(e) => setNewUserRole(e.target.value)}>
                          <MenuItem value="user">User</MenuItem>
                          <MenuItem value="admin">Admin</MenuItem>
                          {me?.role === "owner" && <MenuItem value="owner">Owner</MenuItem>}
                        </Select>
                      </FormControl>
                      <Button type="submit" variant="contained">Create User</Button>
                    </Stack>
                  </Box>
                </CardSection>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <CardSection title={`Users (${users.length})`}>
                  <List dense>
                    {users.map((u) => (
                      <ListItem key={u.id} divider>
                        <ListItemText primary={`${u.email} (${u.role})`} secondary={u.is_active ? "active" : "inactive"} />
                      </ListItem>
                    ))}
                  </List>
                  <Typography variant="subtitle2" sx={{ mt: 1 }}>Permissions</Typography>
                  <List dense>
                    {permissions.map((p) => (
                      <ListItem key={`${p.role}-${p.permission}`} divider>
                        <ListItemText primary={`${p.role}: ${p.permission}`} />
                      </ListItem>
                    ))}
                  </List>
                </CardSection>
              </Grid>
            </Grid>
          )}
        </Stack>
      </Container>
    </Box>
  );
}
