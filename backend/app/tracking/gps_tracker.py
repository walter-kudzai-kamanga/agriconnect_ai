from typing import Dict, Optional, List
from datetime import datetime, timedelta
import asyncio

class GPSTracker:
    """Service for real-time GPS tracking"""
    
    def __init__(self):
        self.active_trackings = {}
        self.tracking_history = {}
    
    def start_tracking(self, job_id: str, transporter_phone: str, 
                      farmer_phone: str, route_info: Dict) -> Dict:
        """Start tracking a transport job"""
        self.active_trackings[job_id] = {
            'transporter_phone': transporter_phone,
            'farmer_phone': farmer_phone,
            'route_info': route_info,
            'current_location': None,
            'last_update': datetime.now(),
            'milestones': self._calculate_milestones(route_info),
            'history': []
        }
        
        return {
            'job_id': job_id,
            'status': 'tracking_started',
            'message': 'GPS tracking activated'
        }
    
    def update_location(self, job_id: str, lat: float, lon: float, 
                       speed: float = None, heading: float = None) -> Dict:
        """Update vehicle location"""
        if job_id not in self.active_trackings:
            return {'error': 'Job not found or tracking not started'}
        
        tracking = self.active_trackings[job_id]
        location_data = {
            'lat': lat,
            'lon': lon,
            'timestamp': datetime.now().isoformat(),
            'speed': speed,
            'heading': heading
        }
        
        tracking['current_location'] = location_data
        tracking['last_update'] = datetime.now()
        tracking['history'].append(location_data)
        
        # Keep only last 100 location points
        if len(tracking['history']) > 100:
            tracking['history'] = tracking['history'][-100:]
        
        # Check if milestone reached
        milestone = self._check_milestone(tracking, lat, lon)
        
        return {
            'job_id': job_id,
            'location': location_data,
            'milestone_reached': milestone is not None,
            'milestone': milestone
        }
    
    def get_tracking_status(self, job_id: str) -> Optional[Dict]:
        """Get current tracking status"""
        if job_id not in self.active_trackings:
            return None
        
        tracking = self.active_trackings[job_id]
        progress = self._calculate_progress(tracking)
        
        return {
            'job_id': job_id,
            'current_location': tracking['current_location'],
            'progress': progress,
            'last_update': tracking['last_update'].isoformat(),
            'milestones': tracking['milestones'],
            'eta': self._calculate_eta(tracking, progress)
        }
    
    def _calculate_milestones(self, route_info: Dict) -> List[Dict]:
        """Calculate key milestones for route"""
        milestones = []
        total_distance = route_info.get('distance_km', 0)
        estimated_duration = route_info.get('estimated_duration_minutes', 120)
        
        for percent in [25, 50, 75, 90]:
            milestones.append({
                'percent': percent,
                'distance_km': total_distance * (percent / 100),
                'estimated_time_minutes': estimated_duration * (percent / 100),
                'reached': False,
                'reached_at': None
            })
        
        return milestones
    
    def _check_milestone(self, tracking: Dict, lat: float, lon: float) -> Optional[Dict]:
        """Check if milestone reached"""
        if not tracking['current_location']:
            return None
        
        # Calculate progress based on distance traveled
        # This is simplified - in production, use actual route distance
        progress = self._calculate_progress(tracking)
        
        for milestone in tracking['milestones']:
            if not milestone['reached'] and progress >= milestone['percent']:
                milestone['reached'] = True
                milestone['reached_at'] = datetime.now().isoformat()
                return milestone
        
        return None
    
    def _calculate_progress(self, tracking: Dict) -> float:
        """Calculate route progress percentage"""
        # Simplified calculation - in production, use actual route distance
        if not tracking['history']:
            return 0.0
        
        # Estimate progress based on time elapsed vs estimated duration
        start_time = datetime.fromisoformat(tracking['history'][0]['timestamp'])
        elapsed = (datetime.now() - start_time).total_seconds() / 60  # minutes
        estimated_duration = tracking['route_info'].get('estimated_duration_minutes', 120)
        
        progress = min((elapsed / estimated_duration) * 100, 95)  # Cap at 95% until delivery
        return round(progress, 1)
    
    def _calculate_eta(self, tracking: Dict, progress: float) -> Optional[str]:
        """Calculate estimated time of arrival"""
        if progress >= 95:
            return "Arriving soon"
        
        estimated_duration = tracking['route_info'].get('estimated_duration_minutes', 120)
        remaining_percent = (100 - progress) / 100
        remaining_minutes = estimated_duration * remaining_percent
        
        if remaining_minutes < 60:
            return f"{int(remaining_minutes)} minutes"
        else:
            hours = int(remaining_minutes / 60)
            mins = int(remaining_minutes % 60)
            return f"{hours}h {mins}m"
    
    def stop_tracking(self, job_id: str):
        """Stop tracking and archive"""
        if job_id in self.active_trackings:
            self.tracking_history[job_id] = self.active_trackings[job_id]
            del self.active_trackings[job_id]
    
    def get_all_active_trackings(self) -> Dict[str, Dict]:
        """Get all active tracking jobs"""
        return {
            job_id: self.get_tracking_status(job_id)
            for job_id in self.active_trackings.keys()
        }

# Global instance
gps_tracker = GPSTracker()

