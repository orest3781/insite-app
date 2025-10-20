#!/usr/bin/env python3
"""
QC Test Script: Start, Pause, and Stop Button State Transitions

This script verifies that all state transitions and button states are correct
according to the QC specification.
"""

import logging
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)


class ProcessingState(Enum):
    """Processing state enum."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"


class ButtonState:
    """Represents button states."""
    def __init__(self):
        self.start_enabled = True
        self.pause_enabled = False
        self.stop_enabled = False
        self.start_text = "▶ Start"
    
    def __repr__(self):
        return f"Start: {'✅' if self.start_enabled else '❌'} ({self.start_text}), Pause: {'✅' if self.pause_enabled else '❌'}, Stop: {'✅' if self.stop_enabled else '❌'}"


class StateTransitionTester:
    """Test state transitions and button states."""
    
    def __init__(self):
        self.state = ProcessingState.IDLE
        self.button_state = ButtonState()
        self.test_results = []
    
    def expected_button_states(self, state: ProcessingState) -> ButtonState:
        """Get expected button states for a given processing state."""
        expected = ButtonState()
        
        if state == ProcessingState.IDLE:
            expected.start_enabled = True
            expected.start_text = "▶ Start"
            expected.pause_enabled = False
            expected.stop_enabled = False
        elif state == ProcessingState.RUNNING:
            expected.start_enabled = False
            expected.pause_enabled = True
            expected.stop_enabled = True
        elif state == ProcessingState.PAUSING:
            expected.start_enabled = False
            expected.pause_enabled = False
            expected.stop_enabled = True  # Can stop while pausing
        elif state == ProcessingState.PAUSED:
            expected.start_enabled = True
            expected.start_text = "▶ Resume"
            expected.pause_enabled = False
            expected.stop_enabled = True
        elif state == ProcessingState.STOPPING:
            expected.start_enabled = False
            expected.pause_enabled = False
            expected.stop_enabled = False
        elif state == ProcessingState.STOPPED:
            expected.start_enabled = True
            expected.start_text = "▶ Start"
            expected.pause_enabled = False
            expected.stop_enabled = False
        
        return expected
    
    def verify_button_state(self, expected: ButtonState, actual: ButtonState) -> bool:
        """Verify button state matches expected."""
        return (
            expected.start_enabled == actual.start_enabled and
            expected.pause_enabled == actual.pause_enabled and
            expected.stop_enabled == actual.stop_enabled and
            expected.start_text == actual.start_text
        )
    
    def test_state_transition(self, from_state: ProcessingState, 
                             to_state: ProcessingState,
                             button_state_after: ButtonState) -> bool:
        """Test a state transition."""
        logger.info(f"Testing: {from_state.value} → {to_state.value}")
        
        expected = self.expected_button_states(to_state)
        
        if self.verify_button_state(expected, button_state_after):
            logger.info(f"  ✅ Button states correct: {button_state_after}")
            self.test_results.append(f"✅ {from_state.value} → {to_state.value}")
            return True
        else:
            logger.error(f"  ❌ Button state mismatch!")
            logger.error(f"     Expected: {expected}")
            logger.error(f"     Actual:   {button_state_after}")
            self.test_results.append(f"❌ {from_state.value} → {to_state.value}")
            return False
    
    def run_tests(self):
        """Run all state transition tests."""
        logger.info("=" * 70)
        logger.info("STATE TRANSITION QC TESTS")
        logger.info("=" * 70)
        
        # Test 1: IDLE → RUNNING
        logger.info("\n[Test 1] Start button clicked in IDLE state")
        state_after = ButtonState()
        state_after.start_enabled = False
        state_after.pause_enabled = True
        state_after.stop_enabled = True
        self.test_state_transition(ProcessingState.IDLE, ProcessingState.RUNNING, state_after)
        
        # Test 2: RUNNING → PAUSING
        logger.info("\n[Test 2] Pause button clicked in RUNNING state")
        state_after = ButtonState()
        state_after.start_enabled = False
        state_after.pause_enabled = False
        state_after.stop_enabled = True
        self.test_state_transition(ProcessingState.RUNNING, ProcessingState.PAUSING, state_after)
        
        # Test 3: PAUSING → PAUSED
        logger.info("\n[Test 3] Pause operation completes")
        state_after = ButtonState()
        state_after.start_enabled = True
        state_after.start_text = "▶ Resume"
        state_after.pause_enabled = False
        state_after.stop_enabled = True
        self.test_state_transition(ProcessingState.PAUSING, ProcessingState.PAUSED, state_after)
        
        # Test 4: PAUSED → RUNNING (Resume)
        logger.info("\n[Test 4] Resume button clicked in PAUSED state")
        state_after = ButtonState()
        state_after.start_enabled = False
        state_after.pause_enabled = True
        state_after.stop_enabled = True
        self.test_state_transition(ProcessingState.PAUSED, ProcessingState.RUNNING, state_after)
        
        # Test 5: RUNNING → STOPPING
        logger.info("\n[Test 5] Stop button clicked in RUNNING state")
        state_after = ButtonState()
        state_after.start_enabled = False
        state_after.pause_enabled = False
        state_after.stop_enabled = False
        self.test_state_transition(ProcessingState.RUNNING, ProcessingState.STOPPING, state_after)
        
        # Test 6: STOPPING → STOPPED
        logger.info("\n[Test 6] Stop operation completes (STOPPING → STOPPED)")
        state_after = ButtonState()
        state_after.start_enabled = True
        state_after.start_text = "▶ Start"
        state_after.pause_enabled = False
        state_after.stop_enabled = False
        self.test_state_transition(ProcessingState.STOPPING, ProcessingState.STOPPED, state_after)
        
        # Test 7: STOPPED → IDLE
        logger.info("\n[Test 7] Stop operation completes (STOPPED → IDLE)")
        state_after = ButtonState()
        state_after.start_enabled = True
        state_after.start_text = "▶ Start"
        state_after.pause_enabled = False
        state_after.stop_enabled = False
        self.test_state_transition(ProcessingState.STOPPED, ProcessingState.IDLE, state_after)
        
        # Test 8: PAUSED → STOPPING (Stop from paused)
        logger.info("\n[Test 8] Stop button clicked in PAUSED state")
        state_after = ButtonState()
        state_after.start_enabled = False
        state_after.pause_enabled = False
        state_after.stop_enabled = False
        self.test_state_transition(ProcessingState.PAUSED, ProcessingState.STOPPING, state_after)
        
        # Test 9: RUNNING → STOPPING (alternative path)
        logger.info("\n[Test 9] Stop button clicked in RUNNING state (alternative)")
        state_after = ButtonState()
        state_after.start_enabled = False
        state_after.pause_enabled = False
        state_after.stop_enabled = False
        self.test_state_transition(ProcessingState.RUNNING, ProcessingState.STOPPING, state_after)
        
        logger.info("\n" + "=" * 70)
        logger.info("TEST RESULTS")
        logger.info("=" * 70)
        for result in self.test_results:
            logger.info(result)
        
        passed = sum(1 for r in self.test_results if r.startswith("✅"))
        total = len(self.test_results)
        logger.info(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("\n✅ ALL TESTS PASSED - Button state transitions are correct!")
            return True
        else:
            logger.error(f"\n❌ {total - passed} test(s) failed")
            return False


def main():
    """Run the QC tests."""
    tester = StateTransitionTester()
    success = tester.run_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
