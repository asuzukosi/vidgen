"""
Pipeline data model
Holds all data related to a video generation operation.
"""

import os
import json
import pickle
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from utils.logger import get_logger

logger = get_logger(__name__)


class PipelineData(BaseModel):
    """
    Comprehensive data model for video generation pipeline.
    
    Holds all data at each stage of the pipeline and provides
    serialization/deserialization capabilities.
    """
    
    # Identification
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Source document
    source_path: Optional[str] = None
    source_type: Optional[str] = None  # 'pdf', 'html', etc.
    
    # Stage 1 & 2: Document Processing
    parsed_content: Optional[Dict[str, Any]] = None  # Structured content from document
    images_metadata: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Stage 3: Content Analysis
    chunks: List[Dict[str, Any]] = Field(default_factory=list)  # Processed chunks
    video_outline: Optional[Dict[str, Any]] = None
    
    # Stage 4: Script & Voiceover
    script_data: Optional[Dict[str, Any]] = None
    script_with_audio: Optional[Dict[str, Any]] = None
    
    # Stage 5: Video Generation
    video_path: Optional[str] = None
    output_path: Optional[str] = None  # Final output video path
    
    # Configuration
    config: Optional[Dict[str, Any]] = None
    
    # Context processor information
    context_processor_info: Optional[Dict[str, Any]] = None  # Stores context processor config and results
    
    # Status tracking
    current_stage: str = "initialized"
    status: str = "pending"  # pending, in_progress, completed, failed
    
    # Timing information
    stage_timings: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # {stage_name: {start_time, end_time, duration}}
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def save_to_folder(self, base_dir: str) -> str:
        """
        Save pipeline data to a folder as JSON files.
        Creates a subfolder named with the pipeline ID.
        
        Args:
            base_dir: Base directory where pipeline data will be saved
        
        Returns:
            Path to the saved data folder
        """
        base_path = Path(base_dir)
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subfolder with pipeline ID
        folder = base_path / self.id
        folder.mkdir(parents=True, exist_ok=True)
        
        # Save main data
        main_file = folder / "pipeline_data.json"
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)
        
        # Save individual components for easy access
        if self.parsed_content:
            with open(folder / "parsed_content.json", 'w', encoding='utf-8') as f:
                json.dump(self.parsed_content, f, indent=2, ensure_ascii=False)
        
        if self.images_metadata:
            images_dir = folder / "images"
            images_dir.mkdir(exist_ok=True)
            with open(images_dir / "images_metadata_labeled.json", 'w', encoding='utf-8') as f:
                json.dump(self.images_metadata, f, indent=2, ensure_ascii=False)
        
        if self.video_outline:
            with open(folder / "video_outline.json", 'w', encoding='utf-8') as f:
                json.dump(self.video_outline, f, indent=2, ensure_ascii=False)
        
        if self.script_data:
            with open(folder / "video_script.json", 'w', encoding='utf-8') as f:
                json.dump(self.script_data, f, indent=2, ensure_ascii=False)
        
        if self.script_with_audio:
            with open(folder / "script_with_audio.json", 'w', encoding='utf-8') as f:
                json.dump(self.script_with_audio, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved pipeline data to {folder}")
        return str(folder)
    
    def save_to_pickle(self, file_path: str) -> str:
        """
        Save pipeline data to a pickle file.
        
        Args:
            file_path: Path to pickle file
        
        Returns:
            Path to the saved pickle file
        """
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path_obj, 'wb') as f:
            pickle.dump(self, f)
        
        logger.info(f"Saved pipeline data to pickle: {file_path}")
        return str(file_path_obj)
    
    @classmethod
    def load_from_folder(cls, folder_path: str) -> 'PipelineData':
        """
        Load pipeline data from a folder.
        Can accept either a base directory with pipeline ID subfolder, or direct path to pipeline folder.
        
        Args:
            folder_path: Path to folder containing pipeline data (can be base_dir/pipeline_id or direct path)
        
        Returns:
            PipelineData instance
        """
        folder = Path(folder_path)
        
        # If folder doesn't exist, try treating it as base_dir/pipeline_id
        if not folder.exists():
            # Check if it's a base directory with UUID subfolder
            base_dir = folder.parent
            pipeline_id = folder.name
            folder = base_dir / pipeline_id
        
        # Try to load main data file
        main_file = folder / "pipeline_data.json"
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)
        
        # Fallback: reconstruct from individual files
        data = {
            "id": folder.name,
            "created_at": datetime.now().isoformat()
        }
        
        parsed_file = folder / "parsed_content.json"
        if parsed_file.exists():
            with open(parsed_file, 'r', encoding='utf-8') as f:
                data["parsed_content"] = json.load(f)
        
        images_file = folder / "images" / "images_metadata_labeled.json"
        if images_file.exists():
            with open(images_file, 'r', encoding='utf-8') as f:
                data["images_metadata"] = json.load(f)
        
        outline_file = folder / "video_outline.json"
        if outline_file.exists():
            with open(outline_file, 'r', encoding='utf-8') as f:
                data["video_outline"] = json.load(f)
        
        script_file = folder / "video_script.json"
        if script_file.exists():
            with open(script_file, 'r', encoding='utf-8') as f:
                data["script_data"] = json.load(f)
        
        audio_file = folder / "script_with_audio.json"
        if audio_file.exists():
            with open(audio_file, 'r', encoding='utf-8') as f:
                data["script_with_audio"] = json.load(f)
        
        logger.info(f"Loaded pipeline data from folder: {folder}")
        return cls(**data)
    
    @classmethod
    def load_by_id(cls, pipeline_id: str, base_dir: str = "temp") -> 'PipelineData':
        """
        Load pipeline data by ID from base directory.
        
        Args:
            pipeline_id: UUID of the pipeline
            base_dir: Base directory containing pipeline folders
        
        Returns:
            PipelineData instance
        
        Raises:
            FileNotFoundError: If pipeline folder doesn't exist
        """
        folder_path = Path(base_dir) / pipeline_id
        if not folder_path.exists():
            raise FileNotFoundError(f"Pipeline folder not found: {folder_path}")
        return cls.load_from_folder(str(folder_path))
    
    @classmethod
    def load_from_pickle(cls, file_path: str) -> 'PipelineData':
        """
        Load pipeline data from a pickle file.
        
        Args:
            file_path: Path to pickle file
        
        Returns:
            PipelineData instance
        """
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        logger.info(f"Loaded pipeline data from pickle: {file_path}")
        return data
    
    def update_stage(self, stage: str, status: str = "in_progress"):
        """
        Update current stage and status, tracking timing.
        
        Args:
            stage: Current stage name
            status: Status (pending, in_progress, completed, failed)
        """
        now = datetime.now().isoformat()
        
        # If starting a new stage
        if status == "in_progress" and stage != self.current_stage:
            if stage not in self.stage_timings:
                self.stage_timings[stage] = {}
            self.stage_timings[stage]['start_time'] = now
        
        # If completing or failing a stage
        if status in ["completed", "failed"]:
            if stage in self.stage_timings and 'start_time' in self.stage_timings[stage]:
                start_time = datetime.fromisoformat(self.stage_timings[stage]['start_time'])
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                self.stage_timings[stage]['end_time'] = now
                self.stage_timings[stage]['duration'] = duration
                self.stage_timings[stage]['status'] = status
        
        self.current_stage = stage
        self.status = status
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the pipeline data.
        
        Returns:
            Dictionary with summary information
        """
        total_duration = sum(
            timing.get('duration', 0) 
            for timing in self.stage_timings.values() 
            if 'duration' in timing
        )
        
        return {
            "id": self.id,
            "created_at": self.created_at,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "current_stage": self.current_stage,
            "status": self.status,
            "output_path": self.output_path,
            "has_parsed_content": self.parsed_content is not None,
            "has_images": len(self.images_metadata) > 0,
            "has_outline": self.video_outline is not None,
            "has_scripts": self.script_data is not None,
            "has_audio": self.script_with_audio is not None,
            "has_video": self.video_path is not None and os.path.exists(self.video_path) if self.video_path else False,
            "stage_timings": self.stage_timings,
            "total_duration": total_duration,
            "context_processor_info": self.context_processor_info
        }

