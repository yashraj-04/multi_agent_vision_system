import time
import math
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from app.agents.base_agent import AgentOutput
from app.conflict.dynamic_reliability import DynamicReliabilityEngine
from app.conflict.conflict_detector import normalize_to_canonical_action
from app.utils.logger import logger

CANONICAL_ACTIONS = {
    "GO", "SLOW DOWN", "STOP", "EMERGENCY BRAKE", "TURN LEFT", "TURN RIGHT", "CHANGE LANE"
}

SAFETY_TIE_BREAK_ORDER = [
    "EMERGENCY BRAKE", "STOP", "SLOW DOWN", "CHANGE LANE", "TURN LEFT", "TURN RIGHT", "GO"
]

class ConflictResolutionEngine:
    """
    Implements 10 research-grade conflict resolution algorithms for multi-agent autonomous driving vision systems.
    Enforces strict closed canonical action mapping, explicit abstentions, safety-first tie breaking, and exact candidate set Bayesian fusion.
    """
    def __init__(self, reliability_engine: Optional[DynamicReliabilityEngine] = None):
        self.reliability_engine = reliability_engine or DynamicReliabilityEngine()

    def resolve(self, agent_outputs: List[AgentOutput], conflicts: List[Dict[str, Any]], strategy: str = "Rule-Based Arbitration") -> Dict[str, Any]:
        start_time = time.perf_counter()
        
        # Standardize proposed action candidates across agents & filter abstentions
        proposals, abstentions = self._normalize_agent_actions(agent_outputs)
        
        if not proposals:
            # Fallback if all agents abstained
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "strategy": strategy,
                "final_decision": "SLOW DOWN",
                "confidence": 0.5,
                "reasoning": "All perception agents abstained. Defensive SLOW DOWN action commanded.",
                "elaborated_summary": "All perception agents abstained from voting.",
                "winning_agent": "System Defensive Fallback",
                "resolution_time_ms": round(elapsed_ms, 2),
                "breakdown": {"abstentions": [a["agent_name"] for a in abstentions]},
                "has_conflicts": len(conflicts) > 0,
                "was_tie": False
            }

        if strategy == "Majority Voting":
            result = self._majority_voting(proposals)
        elif strategy == "Confidence Weighted Voting":
            result = self._confidence_weighted_voting(proposals)
        elif strategy == "Rule-Based Arbitration":
            result = self._rule_based_arbitration(proposals, agent_outputs)
        elif strategy == "Leader Election":
            result = self._leader_election(proposals, agent_outputs)
        elif strategy == "Dynamic Reliability Scoring":
            result = self._dynamic_reliability_scoring(proposals)
        elif strategy == "Bayesian Fusion":
            result = self._bayesian_fusion(proposals)
        elif strategy == "Weighted Consensus":
            result = self._weighted_consensus(proposals)
        elif strategy == "Hybrid Arbitration":
            result = self._hybrid_arbitration(proposals, agent_outputs)
        elif strategy in ["Softmax-Weighted Selection", "Adaptive Reliability Learning"]:
            result = self._softmax_weighted_selection(proposals)
            strategy = "Softmax-Weighted Selection"
        elif strategy == "Dynamic Entropy-Weighted Ensemble":
            result = self._entropy_weighted_ensemble(proposals)
        else:
            result = self._rule_based_arbitration(proposals, agent_outputs)
            strategy = "Rule-Based Arbitration (Fallback)"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        final_act = result["decision"]
        win_auth = result.get("winning_agent", "Multi-Agent Consensus")
        conf_pct = round(result["confidence"] * 100, 1)
        conflict_status = f"{len(conflicts)} conflict event(s) arbitrated" if conflicts else "Full multi-agent alignment"

        elaborated = (
            f"Final Control Action: '{final_act}' (Confidence: {conf_pct}%). "
            f"Arbitrated via Strategy: '{strategy}' by {win_auth}. "
            f"Status: {conflict_status}. Rationale: {result['reasoning']}"
        )

        breakdown = result.get("breakdown", {})
        if abstentions:
            breakdown["abstentions"] = [a["agent_name"] for a in abstentions]

        from app.knowledge.indian_traffic_rules import retrieve_rule_by_scenario, generate_rejection_rationale, INDIAN_TRAFFIC_RULES_KB

        # Determine governing rule based on final decision and conflict context
        if final_act in ["EMERGENCY BRAKE"]:
            rule_info = INDIAN_TRAFFIC_RULES_KB["MVA_SEC_120_VULNERABLE_HAZARD"]
        elif final_act in ["STOP"]:
            rule_info = INDIAN_TRAFFIC_RULES_KB["MVA_SEC_119_RED_SIGNAL"]
        elif final_act in ["SLOW DOWN"]:
            rule_info = INDIAN_TRAFFIC_RULES_KB["IRC_67_CROSSWALK_CAUTION"]
        else:
            rule_info = INDIAN_TRAFFIC_RULES_KB["MVA_SEC_121_LANE_DISCIPLINE"]

        # Build rejected alternatives explanations
        all_candidate_actions = set([p["action"] for p in proposals]) - {final_act}
        rejected_alternatives = {
            alt: generate_rejection_rationale(alt, final_act, rule_info)
            for alt in all_candidate_actions
        }

        decision_trace = {
            "inputs_used": [
                {
                    "agent_name": p["agent_name"],
                    "action": p["action"],
                    "confidence": p["confidence"],
                    "reliability": p["reliability"]
                }
                for p in proposals
            ],
            "rule_fired": {
                "rule_id": rule_info["rule_id"],
                "title": rule_info["title"],
                "source": rule_info["source"],
                "scenario_tag": rule_info["scenario_tag"],
                "rule_text": rule_info["rule_text"]
            },
            "rejected_alternatives": rejected_alternatives
        }

        actuator_command = self._get_actuator_command(final_act)

        return {
            "strategy": strategy,
            "final_decision": final_act,
            "confidence": round(result["confidence"], 3),
            "reasoning": result["reasoning"],
            "elaborated_summary": elaborated,
            "winning_agent": win_auth,
            "resolution_time_ms": round(elapsed_ms, 3),
            "breakdown": breakdown,
            "has_conflicts": len(conflicts) > 0,
            "was_tie": result.get("was_tie", False),
            "decision_trace": decision_trace,
            "actuator_command": actuator_command
        }

    def _get_actuator_command(self, final_act: str) -> Dict[str, Any]:
        act = str(final_act).upper()
        if act in ["GO", "PROCEED", "PROCEED_GREEN_LIGHT", "ROAD_CLEAR"]:
            return {
                "driver_instruction": "PROCEED AT NORMAL SPEED (CLEAR ROAD)",
                "target_speed_kmh": 50,
                "throttle_pct": 65,
                "brake_pct": 0,
                "steering_angle_deg": 0.0,
                "urgency": "NORMAL",
                "theme_color": "green",
                "description": "Safe path confirmed. Accelerate to target speed and maintain lane alignment."
            }
        elif act in ["SLOW DOWN", "SLOW_DOWN", "CROSSWALK_CAUTION", "MODERATE_DISTANCE"]:
            return {
                "driver_instruction": "DECELERATE & PREPARE TO YIELD (REDUCE SPEED)",
                "target_speed_kmh": 20,
                "throttle_pct": 10,
                "brake_pct": 30,
                "steering_angle_deg": 0.0,
                "urgency": "CAUTION",
                "theme_color": "yellow",
                "description": "Cautionary zone or crosswalk detected. Reduce speed and prepare to stop if necessary."
            }
        elif act in ["STOP", "MUST_STOP_RED_LIGHT", "STOP_SIGN"]:
            return {
                "driver_instruction": "MANDATORY FULL STOP AT SIGNAL / INTERSECTION",
                "target_speed_kmh": 0,
                "throttle_pct": 0,
                "brake_pct": 80,
                "steering_angle_deg": 0.0,
                "urgency": "HIGH",
                "theme_color": "red",
                "description": "Mandatory red light or stop sign. Apply service brakes until vehicle reaches complete halt."
            }
        elif act in ["EMERGENCY BRAKE", "EMERGENCY_BRAKE", "IMMEDIATE_HAZARD"]:
            return {
                "driver_instruction": "EMERGENCY BRAKE — IMMEDIATE HAZARD DETECTED!",
                "target_speed_kmh": 0,
                "throttle_pct": 0,
                "brake_pct": 100,
                "steering_angle_deg": 0.0,
                "urgency": "CRITICAL",
                "theme_color": "crimson",
                "description": "Immediate proximity or collision hazard detected! Maximum braking force engaged."
            }
        elif act in ["TURN LEFT"]:
            return {
                "driver_instruction": "EXECUTE CONTROLLED LEFT TURN",
                "target_speed_kmh": 15,
                "throttle_pct": 20,
                "brake_pct": 10,
                "steering_angle_deg": -30.0,
                "urgency": "NORMAL",
                "theme_color": "blue",
                "description": "Steer left into target lane while checking cross-traffic."
            }
        elif act in ["TURN RIGHT"]:
            return {
                "driver_instruction": "EXECUTE CONTROLLED RIGHT TURN",
                "target_speed_kmh": 15,
                "throttle_pct": 20,
                "brake_pct": 10,
                "steering_angle_deg": 30.0,
                "urgency": "NORMAL",
                "theme_color": "blue",
                "description": "Steer right into target lane while checking cross-traffic."
            }
        else:  # CHANGE LANE
            return {
                "driver_instruction": "INITIATE CONTROLLED LANE CHANGE",
                "target_speed_kmh": 35,
                "throttle_pct": 40,
                "brake_pct": 0,
                "steering_angle_deg": 15.0,
                "urgency": "CAUTION",
                "theme_color": "cyan",
                "description": "Signal and transition into adjacent clear lane."
            }

    def _normalize_agent_actions(self, agent_outputs: List[AgentOutput]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Maps specific agent outputs into closed canonical action set.
        Unmapped decisions produce action = None and are excluded from voting (abstentions).
        """
        proposals = []
        abstentions = []
        for a in agent_outputs:
            name = getattr(a, "agent_name", None)
            if name is None and isinstance(a, dict):
                name = a.get("agent_name", "Unknown Agent")

            dec = getattr(a, "decision", None)
            if dec is None and isinstance(a, dict):
                dec = a.get("decision", "")

            conf = getattr(a, "confidence", None)
            if conf is None and isinstance(a, dict):
                conf = a.get("confidence")
            if conf is None:
                conf = 0.8

            reason = getattr(a, "reasoning", None)
            if reason is None and isinstance(a, dict):
                reason = a.get("reasoning", "")

            act = normalize_to_canonical_action(dec)
            rel = self.reliability_engine.get_score(name)

            entry = {
                "agent_name": name,
                "raw_decision": dec,
                "action": act,
                "confidence": float(conf),
                "reliability": float(rel),
                "reasoning": reason
            }

            if act is not None and act in CANONICAL_ACTIONS:
                proposals.append(entry)
            else:
                abstentions.append(entry)

        return proposals, abstentions

    def _resolve_tie(self, scores: Dict[str, float]) -> Tuple[str, bool]:
        """Enforces shared safety-first tie-breaking policy: EMERGENCY BRAKE > STOP > SLOW DOWN > CHANGE LANE > TURN LEFT > TURN RIGHT > GO."""
        if not scores:
            return "SLOW DOWN", False
        max_val = max(scores.values())
        tied_candidates = [act for act, sc in scores.items() if abs(sc - max_val) < 1e-6]
        if len(tied_candidates) > 1:
            for priority_act in SAFETY_TIE_BREAK_ORDER:
                if priority_act in tied_candidates:
                    return priority_act, True
            return tied_candidates[0], True
        return tied_candidates[0], False

    # 1. Majority Voting
    def _majority_voting(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        counts = {}
        for p in proposals:
            act = p["action"]
            counts[act] = counts.get(act, 0) + 1
            
        winning_action, was_tie = self._resolve_tie(counts)
        win_count = counts[winning_action]
        conf = win_count / len(proposals)
        
        return {
            "decision": winning_action,
            "confidence": conf,
            "reasoning": f"Majority Voting selected '{winning_action}' with {win_count}/{len(proposals)} agent votes." + (" (Safety tie-break applied)" if was_tie else ""),
            "breakdown": counts,
            "was_tie": was_tie
        }

    # 2. Confidence Weighted Voting
    def _confidence_weighted_voting(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        scores = {}
        total_conf = 0.0
        for p in proposals:
            act = p["action"]
            c = p["confidence"]
            scores[act] = scores.get(act, 0.0) + c
            total_conf += c
            
        winning_action, was_tie = self._resolve_tie(scores)
        normalized_conf = scores[winning_action] / max(total_conf, 0.01)
        
        return {
            "decision": winning_action,
            "confidence": min(1.0, normalized_conf * 1.1),
            "reasoning": f"Confidence Weighted Voting accumulated weight {scores[winning_action]:.2f} for '{winning_action}'.",
            "breakdown": scores,
            "was_tie": was_tie
        }

    # 3. Rule-Based Arbitration
    def _rule_based_arbitration(self, proposals: List[Dict[str, Any]], outputs: List[AgentOutput]) -> Dict[str, Any]:
        risk_agent = next((p for p in proposals if p["agent_name"] == "Risk Assessment Agent"), None)
        rule_agent = next((p for p in proposals if p["agent_name"] == "Traffic Rule Agent"), None)
        
        if risk_agent and risk_agent["action"] == "EMERGENCY BRAKE":
            return {
                "decision": "EMERGENCY BRAKE",
                "confidence": 0.99,
                "reasoning": "Rule Arbitration Priority 1 Override: Risk Assessment Agent identified imminent collision.",
                "winning_agent": "Risk Assessment Agent",
                "was_tie": False
            }
            
        if rule_agent and rule_agent["action"] == "STOP":
            return {
                "decision": "STOP",
                "confidence": 0.97,
                "reasoning": "Rule Arbitration Priority 2 Override: Traffic Rule Agent commanded mandatory STOP.",
                "winning_agent": "Traffic Rule Agent",
                "was_tie": False
            }
            
        scores = {p["action"]: p["confidence"] for p in proposals}
        winning_action, was_tie = self._resolve_tie(scores)
        best_p = next(p for p in proposals if p["action"] == winning_action)

        return {
            "decision": winning_action,
            "confidence": best_p["confidence"],
            "reasoning": f"Rule Arbitration selected '{winning_action}' from highest confidence agent ({best_p['agent_name']}).",
            "winning_agent": best_p["agent_name"],
            "was_tie": was_tie
        }

    # 4. Leader Election
    def _leader_election(self, proposals: List[Dict[str, Any]], outputs: List[AgentOutput]) -> Dict[str, Any]:
        scores = {p["agent_name"]: p["reliability"] * p["confidence"] for p in proposals}
        best_agent_name, was_tie = self._resolve_tie({p["action"]: p["reliability"] * p["confidence"] for p in proposals})
        leader = next(p for p in proposals if p["action"] == best_agent_name)

        return {
            "decision": leader["action"],
            "confidence": leader["confidence"],
            "reasoning": f"Leader Election appointed '{leader['agent_name']}' (Leader Score: {scores[leader['agent_name']]:.2f}) as authority.",
            "winning_agent": leader["agent_name"],
            "was_tie": was_tie
        }

    # 5. Dynamic Reliability Scoring
    def _dynamic_reliability_scoring(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        weighted_scores = {}
        total_weight = 0.0
        for p in proposals:
            w = p["confidence"] * p["reliability"]
            act = p["action"]
            weighted_scores[act] = weighted_scores.get(act, 0.0) + w
            total_weight += w
            
        winning_action, was_tie = self._resolve_tie(weighted_scores)
        conf = weighted_scores[winning_action] / max(total_weight, 0.01)
        
        return {
            "decision": winning_action,
            "confidence": min(1.0, conf),
            "reasoning": f"Dynamic Reliability Scoring favored '{winning_action}' based on historical agent accuracy profiles.",
            "breakdown": weighted_scores,
            "was_tie": was_tie
        }

    # 6. Bayesian Fusion (Candidates restricted to proposed actions only)
    def _bayesian_fusion(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        candidate_actions = list(set(p["action"] for p in proposals if p["action"]))
        if not candidate_actions:
            return {"decision": "SLOW DOWN", "confidence": 0.5, "reasoning": "No valid candidates.", "was_tie": False}

        action_scores = {act: 0.0 for act in candidate_actions}

        for p in proposals:
            p_act = p["action"]
            conf = min(0.99, max(0.01, p["confidence"]))
            rel = min(0.99, max(0.01, p["reliability"]))
            effective_conf = min(0.99, max(0.01, conf * rel))
            
            # Log likelihood ratio update
            lr = math.log(effective_conf / (1.0 - effective_conf))
            
            for act in candidate_actions:
                if act == p_act:
                    action_scores[act] += lr
                else:
                    action_scores[act] -= (lr / max(1, len(candidate_actions) - 1))

        winning_action, was_tie = self._resolve_tie(action_scores)

        # Softmax normalization over candidates strictly
        max_score = max(action_scores.values())
        exp_scores = {act: math.exp(sc - max_score) for act, sc in action_scores.items()}
        sum_exp = sum(exp_scores.values())
        posterior_prob = exp_scores[winning_action] / max(sum_exp, 1e-5)
        
        return {
            "decision": winning_action,
            "confidence": round(posterior_prob, 3),
            "reasoning": f"Bayesian Fusion integrated likelihood ratios over proposed candidates yielding posterior for '{winning_action}'.",
            "breakdown": action_scores,
            "was_tie": was_tie
        }

    # 7. Weighted Consensus
    def _weighted_consensus(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        weights = [p["confidence"] * p["reliability"] for p in proposals]
        total_w = sum(weights)
        norm_weights = [w / max(total_w, 1e-5) for w in weights]
        
        scores = {}
        for p, w in zip(proposals, norm_weights):
            act = p["action"]
            scores[act] = scores.get(act, 0.0) + w
            
        winning_action, was_tie = self._resolve_tie(scores)
        return {
            "decision": winning_action,
            "confidence": round(scores[winning_action], 3),
            "reasoning": f"Weighted Consensus achieved convergence for '{winning_action}' with weight {scores[winning_action]:.2f}.",
            "breakdown": scores,
            "was_tie": was_tie
        }

    # 8. Hybrid Arbitration
    def _hybrid_arbitration(self, proposals: List[Dict[str, Any]], outputs: List[AgentOutput]) -> Dict[str, Any]:
        safety_override = self._rule_based_arbitration(proposals, outputs)
        if safety_override["decision"] in ["EMERGENCY BRAKE", "STOP"]:
            safety_override["reasoning"] = f"[Hybrid Gatekeeper] " + safety_override["reasoning"]
            return safety_override

        return self._dynamic_reliability_scoring(proposals)

    # 9. Softmax-Weighted Selection
    def _softmax_weighted_selection(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        scores = {}
        for p in proposals:
            act = p["action"]
            logit = (p["reliability"] * 1.5) + (p["confidence"] * 1.0)
            scores[act] = scores.get(act, 0.0) + math.exp(logit)
            
        total_exp = sum(scores.values())
        winning_action, was_tie = self._resolve_tie(scores)
        prob = scores[winning_action] / max(total_exp, 1e-5)
        
        return {
            "decision": winning_action,
            "confidence": round(prob, 3),
            "reasoning": f"Softmax-Weighted Selection selected '{winning_action}' with softmax probability {prob:.2f}.",
            "breakdown": scores,
            "was_tie": was_tie
        }

    # 10. Dynamic Entropy-Weighted Ensemble
    def _entropy_weighted_ensemble(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        weights = []
        for p in proposals:
            c = min(0.99, max(0.01, p["confidence"]))
            entropy = - (c * math.log2(c) + (1-c) * math.log2(1-c))
            w = (1.0 / (entropy + 1e-3)) * p["reliability"]
            weights.append(w)
            
        total_w = sum(weights)
        scores = {}
        for p, w in zip(proposals, weights):
            act = p["action"]
            scores[act] = scores.get(act, 0.0) + (w / max(total_w, 1e-5))
            
        winning_action, was_tie = self._resolve_tie(scores)
        return {
            "decision": winning_action,
            "confidence": round(scores[winning_action], 3),
            "reasoning": f"Entropy-Weighted Ensemble favored low-uncertainty action '{winning_action}'.",
            "breakdown": scores,
            "was_tie": was_tie
        }
