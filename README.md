# Houdini MCP marketplace

[HoudiniMCP](https://github.com/JuyeongYi/HoudiniMCP) 의 툴 팩마다 **언제·어떻게 그 툴을 쓰는지** 알려 주는
Claude Code 스킬과 서브에이전트를 플러그인으로 묶어 제공하는 마켓플레이스다. 툴 자체(MCP 서버와
Houdini 패키지)는 HoudiniMCP 저장소에 있고, 이 저장소에는 그 툴을 가르치는 문서만 있다.

두 저장소를 나눈 이유: 청중이 다르다. Houdini 쪽은 `packages/` 만 필요하고 Claude Code 쪽은
스킬만 필요하다. 한 저장소에 두면 플러그인 설치가 팩의 파이썬 코드까지 복사하고, Houdini 는
스킬 폴더를 스캔하고, 스킬 한 줄 고치는 커밋이 툴 코드 히스토리에 섞인다.

English: [README.en.md](README.en.md)

## 설치

```text
/plugin marketplace add JuyeongYi/houdini_mcp_marketplace
/plugin install houdini-mcp@houdini-mcp
/plugin install houdini-mcp-dop@houdini-mcp
```

- 팩 플러그인은 `houdini-mcp` 와 `houdini-mcp-base` 에 의존하므로 함께 설치된다.
- 플러그인은 툴을 **가르치기만** 한다. 툴은 Houdini 세션에 HoudiniMCP 패키지가 로드돼 있어야 나온다.
  설치는 HoudiniMCP 의 README 를 따른다.
- `houdini-mcp` 가 MCP 서버 연결(`plugins/houdini-mcp/.mcp.json`, `http://127.0.0.1:<port>/mcp`)을
  선언한다. 포트는 플러그인 옵션(기본 `22926`, 서버의 `HOUDINI_MCP_PORT`). 프로젝트 `.mcp.json` 이
  같은 서버를 연결하고 있으면 툴이 두 접두사로 두 번 보이니 한쪽만 쓴다.

갱신:

```text
/plugin marketplace update houdini-mcp
/plugin update houdini-mcp-dop@houdini-mcp
```

설치된 사본은 `plugin.json` 의 `version` 이 바뀔 때만 갱신된다. **스킬이나 에이전트를 고치면 그
플러그인의 `version` 을 올린다.**

## 플러그인

```
plugins/<플러그인>/
  .claude-plugin/plugin.json     매니페스트 (이름 houdini-mcp-<도메인>)
  skills/<스킬>/SKILL.md         스킬
  agents/<에이전트>.md            서브에이전트 (필요한 곳만)
```

| 플러그인 | HoudiniMCP 팩 | 스킬 | 서브에이전트 |
|---|---|---|---|
| `houdini-mcp` | `houdini_mcp` | `houdini-mcp-workflow` (+ MCP 서버 연결) | |
| `houdini-mcp-base` | `houdini_mcp_base` | `visual-review`, `scene-debugging` | `houdini-scene-auditor` |
| `houdini-mcp-sop` | `houdini_mcp_sop` | `sop-procedural-modeling` | |
| `houdini-mcp-vex` | `houdini_mcp_vex` | `vex-wrangle-authoring` | |
| `houdini-mcp-mat` | `houdini_mcp_mat` | `materialx-lookdev` | |
| `houdini-mcp-lop` | `houdini_mcp_lop` | `usd-stage-debugging` | |
| `houdini-mcp-render` | `houdini_mcp_render` | `render-and-verify` | `render-qc` |
| `houdini-mcp-dop` | `houdini_mcp_dop` | `dop-simulation-setup` | `simulation-debugger` |
| `houdini-mcp-dop-rbd` | `houdini_mcp_dop_rbd` | `rbd-destruction` | `rbd-diagnostician` |
| `houdini-mcp-hda` | `houdini_mcp_hda` | `hda-authoring` | |
| `houdini-mcp-rig` | `houdini_mcp_rig` | `kinefx-apex-rigging` | |
| `houdini-mcp-chop` | `houdini_mcp_chop` | `channel-analysis` | |
| `houdini-mcp-io` | `houdini_mcp_io` | `export-and-verify` | |
| `houdini-mcp-cop` | `houdini_mcp_cop` | `copernicus-textures` | |

## 툴과 어긋나지 않게

저장소가 둘이라 툴 개명을 스킬이 따라가지 못해도 아무것도 깨지지 않는다. 그래서
`scripts/check_tools.py` 가 그 이음새를 검사한다: HoudiniMCP 소스에서 툴·인자 이름을 읽어(그쪽의
`scripts/gen_pack_readmes.py`, Houdini 불필요) 스킬·에이전트가 백틱으로 적은 snake_case 식별자가
전부 존재하는지 본다. 툴도 인자도 아닌 이름(예시로 든 노드 이름 등)은
`scripts/tool_check_allowlist.txt` 에 적는다.

```text
python scripts/check_tools.py                    # ../HoudiniMCP 를 읽는다
python scripts/check_tools.py --mcp-repo <경로>
claude plugin validate . --strict                # 마켓플레이스
claude plugin validate plugins/houdini-mcp-dop --strict
```

스킬을 고치거나 HoudiniMCP 에서 툴을 바꾼 뒤에는 둘 다 돌린다.

## 작성 규칙

- 플러그인 내용은 영어로 쓴다.
- 스킬은 Houdini 에서 실측한 것이나 툴이 스스로 말하는 것만 적는다. 툴 목록과 인자는 HoudiniMCP 의
  팩별 `README.md`(생성물)에 있으니, 스킬은 언제·어떻게 쓰는지를 설명하고 인자를 나열하지 않는다.
- 툴 이름은 접두사 없이 맨 이름으로 적는다(`make_video`). 접두사는 서버를 어떻게 연결했는지에 따라 다르다.
