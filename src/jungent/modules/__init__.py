"""Reasoning modules for Hammer & Scissors."""

from .base import Module, ModuleRegistry, PipelineContext
from .hammer_scissors import HammerAndScissorsModule
from .instruction_funnel import InstructionFunnelModule

__all__ = [
    "Module",
    "ModuleRegistry",
    "PipelineContext",
    "HammerAndScissorsModule",
    "InstructionFunnelModule",
]
