import contextlib
import hashlib
import json
import os
from collections import OrderedDict
from pathlib import Path
from tempfile import NamedTemporaryFile

TABLE_CACHE_FORMAT_VERSION = 1


class TableCacheError(Exception):
    """A persisted LR table is missing, corrupt, or incompatible with its grammar."""


def grammar_fingerprint(grammar):
    """A stable digest of every source file from which ``grammar`` was loaded.

    A table contains production and state identifiers, so file modification times
    are not enough to prove that it matches a grammar.  The fingerprint covers the
    entire import closure, sorted by path to make it independent of import order.
    """
    digest = hashlib.sha256()
    for file_name in sorted(grammar.imported_files):
        path = Path(file_name)
        try:
            contents = path.read_bytes()
        except OSError as exc:
            raise TableCacheError(f"cannot read grammar source {path}: {exc}") from exc
        digest.update(str(path.resolve()).encode("utf-8"))
        digest.update(b"\0")
        digest.update(contents)
        digest.update(b"\0")
    return digest.hexdigest()


def table_cache_metadata(grammar, build_options):
    """The compatibility metadata persisted alongside a generated LR table."""
    return {
        "format_version": TABLE_CACHE_FORMAT_VERSION,
        "grammar_fingerprint": grammar_fingerprint(grammar),
        "build_options": build_options,
    }


def table_to_serializable(table):
    """Convert table object to serializable representation composed of
    lists and dicts."""
    # states
    states = []
    for state in table.states:
        states.append(_dump_state(state))

    return states


def save_table(file_name, table, metadata):
    """Atomically save a versioned table cache next to a grammar or at a chosen path."""
    target = Path(file_name)
    payload = {**metadata, "table": table_to_serializable(table)}
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            delete=False,
        ) as temporary:
            json.dump(payload, temporary, sort_keys=True)
            temporary_name = temporary.name
        os.replace(temporary_name, target)
    except OSError:
        with contextlib.suppress(UnboundLocalError, OSError):
            os.unlink(temporary_name)
        raise


def table_from_serializable(serialized_states, grammar):
    """Convert serializable representation of a parsing table into
    LRTable object."""
    from parglare.tables import Action, LRState, LRTable

    states = []
    states_dict = {}
    for json_state in serialized_states:
        state = LRState(
            grammar,
            json_state["state_id"],
            grammar.get_symbol(json_state["symbol"]),
        )
        states_dict[state.state_id] = state
        state.finish_flags = json_state["finish_flags"]
        state.actions = json_state["actions"]
        state.gotos = json_state["gotos"]
        states.append(state)

    # Unpack actions and gotos
    for state in states:
        actions = OrderedDict()
        for json_action_fqn in state.actions:
            terminal_fqn, json_actions = json_action_fqn
            term_acts = []
            for json_action in json_actions:
                if "state_id" in json_action:
                    act_state = states_dict[json_action["state_id"]]
                else:
                    act_state = None
                if "prod_id" in json_action:
                    act_prod = grammar.productions[json_action["prod_id"]]
                else:
                    act_prod = None
                term_acts.append(Action(json_action["action"], act_state, act_prod))

            actions[grammar.get_terminal(terminal_fqn)] = term_acts
        state.actions = actions

        gotos = OrderedDict()
        for json_goto_fqn in state.gotos:
            nonterm_fqn, goto_state = json_goto_fqn
            gotos[grammar.get_nonterminal(nonterm_fqn)] = states_dict[goto_state]
        state.gotos = gotos

    table = LRTable(states, calc_finish_flags=False)

    return table


def load_table(file_name, grammar, metadata):
    """Load a table only when its version, grammar closure, and build options match."""
    try:
        with open(file_name, encoding="utf-8") as source:
            payload = json.load(source)
    except (OSError, json.JSONDecodeError) as exc:
        raise TableCacheError(f"cannot read table cache {file_name}: {exc}") from exc

    if not isinstance(payload, dict):
        raise TableCacheError(
            f"{file_name} uses the obsolete unversioned table-cache format"
        )
    if payload.get("format_version") != TABLE_CACHE_FORMAT_VERSION:
        raise TableCacheError(f"{file_name} has an unsupported table-cache format")
    if payload.get("grammar_fingerprint") != metadata["grammar_fingerprint"]:
        raise TableCacheError(f"{file_name} was generated for a different grammar")
    if payload.get("build_options") != metadata["build_options"]:
        raise TableCacheError(
            f"{file_name} was generated with different table-building options"
        )
    if not isinstance(payload.get("table"), list):
        raise TableCacheError(f"{file_name} has no valid serialized table")

    try:
        return table_from_serializable(payload["table"], grammar)
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise TableCacheError(f"{file_name} is structurally invalid: {exc}") from exc


def _dump_state(state):
    s = {}
    s["state_id"] = state.state_id
    s["symbol"] = state.symbol.fqn
    action_items = list(state.actions.items())
    s["actions"] = [
        [terminal.fqn, _dump_actions(actions)] for terminal, actions in action_items
    ]
    goto_items = list(state.gotos.items())
    s["gotos"] = [[nonterminal.fqn, st.state_id] for nonterminal, st in goto_items]
    s["finish_flags"] = state.finish_flags

    return s


def _dump_actions(actions):
    alist = []
    for action in actions:
        a = {}
        a["action"] = action.action
        if action.state is not None:
            a["state_id"] = action.state.state_id
        if action.prod is not None:
            a["prod_id"] = action.prod.prod_id
        alist.append(a)

    return alist
