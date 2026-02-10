"""
Dialogue Manager
Handles conversation state and confirmation flows for critical operations
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
import time
import logging

from .nlu_engine import Intent, ParsedCommand

logger = logging.getLogger(__name__)


class DialogueState(Enum):
    """Current state of dialogue"""
    LISTENING = "listening"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    WAITING_CLARIFICATION = "waiting_clarification"
    COMPLETED = "completed"


@dataclass
class DialogueContext:
    """Maintains dialogue state and context"""
    state: DialogueState = DialogueState.LISTENING
    pending_action: Optional[ParsedCommand] = None
    conversation_history: List[str] = field(default_factory=list)
    retry_count: int = 0
    timestamp: float = field(default_factory=time.time)
    user_id: Optional[str] = None
    
    def reset(self):
        """Reset context to initial state"""
        self.state = DialogueState.LISTENING
        self.pending_action = None
        self.retry_count = 0
        self.timestamp = time.time()


class DialogueManager:
    """Manages conversation flow and confirmations"""
    
    def __init__(
        self,
        tts_engine,
        confirmation_timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize dialogue manager
        
        Args:
            tts_engine: Text-to-speech engine for responses
            confirmation_timeout: Seconds to wait for confirmation
            max_retries: Max retry attempts for failed commands
        """
        self.tts = tts_engine
        self.timeout = confirmation_timeout
        self.max_retries = max_retries
        
        # Actions requiring confirmation
        self.critical_intents = {
            Intent.UPDATE_INVENTORY,
            Intent.WORK_ORDER_COMPLETE,
            Intent.MOVE_ITEM
        }
        
        # Dialogue contexts per user
        self.contexts: Dict[str, DialogueContext] = {}
        
        # Action handlers (to be registered)
        self.action_handlers: Dict[Intent, Callable] = {}
        
    def register_handler(self, intent: Intent, handler: Callable):
        """
        Register action handler for intent
        
        Args:
            intent: Intent type
            handler: Async function to execute action
        """
        self.action_handlers[intent] = handler
        logger.info(f"Registered handler for {intent.value}")
        
    def process_command(
        self,
        parsed_command: ParsedCommand,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Process parsed command through dialogue flow
        
        Args:
            parsed_command: Parsed NLU command
            user_id: User identifier
            
        Returns:
            Response dictionary
        """
        # Get or create context
        if user_id not in self.contexts:
            self.contexts[user_id] = DialogueContext(user_id=user_id)
        
        context = self.contexts[user_id]
        
        # Add to conversation history
        context.conversation_history.append(parsed_command.raw_text)
        
        # Handle based on current state
        if context.state == DialogueState.LISTENING:
            return self._handle_new_command(parsed_command, context)
        
        elif context.state == DialogueState.CONFIRMING:
            return self._handle_confirmation(parsed_command, context)
        
        elif context.state == DialogueState.WAITING_CLARIFICATION:
            return self._handle_clarification(parsed_command, context)
        
        else:
            logger.warning(f"Unexpected state: {context.state}")
            context.reset()
            return {"status": "error", "message": "System reset, please try again"}
    
    def _handle_new_command(
        self,
        command: ParsedCommand,
        context: DialogueContext
    ) -> Dict[str, Any]:
        """Handle new command in listening state"""
        
        # Check if command requires confirmation
        if command.intent in self.critical_intents:
            context.state = DialogueState.CONFIRMING
            context.pending_action = command
            context.timestamp = time.time()
            
            response = self._generate_confirmation_prompt(command)
            self.tts.speak(response["message"])
            
            return response
        
        # Non-critical: execute immediately
        else:
            return self._execute_action(command, context)
    
    def _handle_confirmation(
        self,
        response: ParsedCommand,
        context: DialogueContext
    ) -> Dict[str, Any]:
        """Handle confirmation response"""
        
        # Check timeout
        if time.time() - context.timestamp > self.timeout:
            context.reset()
            msg = "Confirmation timeout. Request cancelled."
            self.tts.speak(msg)
            return {"status": "timeout", "message": msg}
        
        # Parse confirmation
        text_lower = response.raw_text.lower()
        
        if self._is_affirmative(text_lower):
            # Execute pending action
            result = self._execute_action(context.pending_action, context)
            context.reset()
            return result
        
        elif self._is_negative(text_lower):
            # Cancel action
            context.reset()
            msg = "Action cancelled"
            self.tts.speak(msg)
            return {"status": "cancelled", "message": msg}
        
        else:
            # Unclear response - retry
            context.retry_count += 1
            
            if context.retry_count >= self.max_retries:
                context.reset()
                msg = "Too many unclear responses. Request cancelled."
                self.tts.speak(msg)
                return {"status": "max_retries", "message": msg}
            
            msg = "Please say 'yes' to confirm or 'no' to cancel"
            self.tts.speak(msg)
            return {
                "status": "awaiting_confirmation",
                "message": msg,
                "retry": context.retry_count
            }
    
    def _handle_clarification(
        self,
        response: ParsedCommand,
        context: DialogueContext
    ) -> Dict[str, Any]:
        """Handle clarification response"""
        # TODO: Implement clarification logic
        context.reset()
        return {"status": "clarified", "message": "Processing clarification"}
    
    def _execute_action(
        self,
        command: ParsedCommand,
        context: DialogueContext
    ) -> Dict[str, Any]:
        """Execute the action for given command"""
        
        context.state = DialogueState.EXECUTING
        
        # Get handler
        handler = self.action_handlers.get(command.intent)
        
        if not handler:
            msg = f"No handler registered for {command.intent.value}"
            logger.error(msg)
            context.state = DialogueState.LISTENING
            return {"status": "error", "message": msg}
        
        try:
            # Execute handler
            result = handler(command)
            
            # Generate response
            response = self._generate_success_response(command, result)
            self.tts.speak(response["message"])
            
            context.state = DialogueState.COMPLETED
            
            return response
        
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            msg = f"Failed to execute action: {str(e)}"
            self.tts.speak(msg)
            context.state = DialogueState.LISTENING
            
            return {"status": "error", "message": msg}
    
    def _generate_confirmation_prompt(
        self,
        command: ParsedCommand
    ) -> Dict[str, Any]:
        """Generate confirmation prompt for command"""
        
        if command.intent == Intent.UPDATE_INVENTORY:
            sku = command.get_entity("sku")
            qty = command.get_entity("quantity")
            operation = command.get_entity("operation")
            location = command.get_entity("location")
            
            sku_val = sku.value if sku else "unknown item"
            qty_val = qty.value if qty else "unknown quantity"
            op_val = operation.value if operation else "update"
            loc_val = location.value if location else ""
            
            location_text = f" at location {loc_val}" if loc_val else ""
            
            message = (
                f"Confirm: {op_val} {qty_val} units of {sku_val}"
                f"{location_text}. Say yes to proceed or no to cancel."
            )
        
        elif command.intent == Intent.WORK_ORDER_COMPLETE:
            message = "Confirm: Mark current work order as complete. Say yes or no."
        
        elif command.intent == Intent.MOVE_ITEM:
            item = command.get_entity("sku") or command.get_entity("pallet")
            location = command.get_entity("location")
            
            item_val = item.value if item else "item"
            loc_val = location.value if location else "unknown location"
            
            message = f"Confirm: Move {item_val} to {loc_val}. Say yes or no."
        
        else:
            message = "Confirm this action? Say yes or no."
        
        return {
            "status": "awaiting_confirmation",
            "message": message,
            "pending_action": command.intent.value
        }
    
    def _generate_success_response(
        self,
        command: ParsedCommand,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate success response message"""
        
        if command.intent == Intent.QUERY_INVENTORY:
            sku = command.get_entity("sku")
            quantity = result.get("quantity", "unknown")
            location = result.get("location", "unknown location")
            
            message = f"We have {quantity} units of {sku.value} in {location}"
        
        elif command.intent == Intent.UPDATE_INVENTORY:
            sku = command.get_entity("sku")
            qty = command.get_entity("quantity")
            operation = command.get_entity("operation")
            
            message = f"Updated: {operation.value} {qty.value} units of {sku.value}"
        
        elif command.intent == Intent.QUERY_LOCATION:
            item = command.get_entity("sku") or command.get_entity("pallet")
            location = result.get("location", "unknown")
            
            message = f"{item.value} is in location {location}"
        
        elif command.intent == Intent.WORK_ORDER_NEXT:
            task_desc = result.get("description", "No pending tasks")
            message = f"Your next task: {task_desc}"
        
        elif command.intent == Intent.WORK_ORDER_COMPLETE:
            message = "Work order marked as complete"
        
        else:
            message = result.get("message", "Action completed successfully")
        
        return {
            "status": "success",
            "message": message,
            "data": result
        }
    
    def _is_affirmative(self, text: str) -> bool:
        """Check if response is affirmative"""
        affirmatives = ["yes", "yeah", "yep", "correct", "confirm", "ok", "okay"]
        return any(word in text for word in affirmatives)
    
    def _is_negative(self, text: str) -> bool:
        """Check if response is negative"""
        negatives = ["no", "nope", "cancel", "stop", "negative"]
        return any(word in text for word in negatives)
    
    def get_context(self, user_id: str) -> Optional[DialogueContext]:
        """Get dialogue context for user"""
        return self.contexts.get(user_id)
    
    def clear_context(self, user_id: str):
        """Clear dialogue context for user"""
        if user_id in self.contexts:
            del self.contexts[user_id]
            logger.info(f"Cleared context for user {user_id}")


if __name__ == "__main__":
    # Test dialogue manager
    from .tts_engine import IndustrialTTS
    
    tts = IndustrialTTS()
    dm = DialogueManager(tts)
    
    print("Dialogue Manager initialized")
    print(f"Critical intents: {[i.value for i in dm.critical_intents]}")
