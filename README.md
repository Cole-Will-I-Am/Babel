# Babel

Autonomous multi-model collaboration workspace for building the Babel language in `Cole-Will-I-Am/Babel`.

## Model Topology

- Team A draft: `kimi` + `nemotron`
- Team B review/signoff: `deepseek` + `minimadmax`
- Git executor (model-delegated): `minimadmax` via Codex + Ollama

## Loop Behavior

- `orchestrator/run_babel_round.py` runs one full autonomous cycle.
- Team B must dual-signoff before release artifacts are accepted.
- Commit/push is delegated to an Ollama model (default), not direct runner git.
- Persistent memory:
  - `memory/agents/<agent>/notes.md`
  - `memory/agents/<agent>/summary.md`
  - runtime logs (gitignored): `events.jsonl`, `context.jsonl`, `sessions.jsonl`

## 5-Minute Scheduler (Initial Test)

1. Install timer/service:

```bash
cd /root/ai-lab/Babel
./automation/install_systemd.sh
```

2. Confirm timer:

```bash
systemctl list-timers --all | rg babel-autonomy
```

3. Check run logs:

```bash
journalctl -u babel-autonomy.service -n 100 --no-pager
```

## Change to 20 Minutes

Edit [babel-autonomy.timer](/root/ai-lab/Babel/systemd/babel-autonomy.timer) and change:

- `OnCalendar=*:0/5` -> `OnCalendar=*:0/20`

Then reload:

```bash
sudo systemctl daemon-reload
sudo systemctl restart babel-autonomy.timer
```

## Manual Trigger

```bash
cd /root/ai-lab/Babel
./automation/run_once.sh
```

## Main Configuration

- [round_config.json](/root/ai-lab/Babel/orchestrator/round_config.json)
- [active_task.txt](/root/ai-lab/Babel/prompts/active_task.txt)
