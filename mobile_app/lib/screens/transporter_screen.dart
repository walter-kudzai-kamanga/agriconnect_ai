import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

class TransporterScreen extends StatefulWidget {
  const TransporterScreen({super.key});

  @override
  State<TransporterScreen> createState() => _TransporterScreenState();
}

class _TransporterScreenState extends State<TransporterScreen> {
  List<dynamic> _availableJobs = [];
  bool _isLoading = false;
  bool _isAvailable = true;

  @override
  void initState() {
    super.initState();
    _loadAvailableJobs();
  }

  Future<void> _loadAvailableJobs() async {
    setState(() {
      _isLoading = true;
    });

    try {
      // In a real app, this would fetch actual available jobs from the backend
      await Future.delayed(const Duration(seconds: 2));
      
      // Mock data for demonstration
      setState(() {
        _availableJobs = [
          {
            'id': 1,
            'crop_type': 'tomatoes',
            'quantity_kg': 500.0,
            'pickup_location': 'Mashonaland East',
            'destination': 'Mbare Musika',
            'distance_km': 45.0,
            'estimated_fare': 120.0,
          },
          {
            'id': 2,
            'crop_type': 'maize',
            'quantity_kg': 1000.0,
            'pickup_location': 'Mashonaland Central',
            'destination': 'Sakubva Market',
            'distance_km': 85.0,
            'estimated_fare': 200.0,
          },
        ];
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error loading jobs: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _toggleAvailability() {
    setState(() {
      _isAvailable = !_isAvailable;
    });
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(_isAvailable ? 'You are now available' : 'You are now unavailable'),
        backgroundColor: _isAvailable ? Colors.green : Colors.orange,
      ),
    );
  }

  void _acceptJob(int jobId) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Accepted job #$jobId'),
        backgroundColor: Colors.green,
      ),
    );
    
    // Remove the job from available list
    setState(() {
      _availableJobs.removeWhere((job) => job['id'] == jobId);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Text(
                  'Transporter Dashboard',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.green,
                  ),
                ),
                const Spacer(),
                Switch(
                  value: _isAvailable,
                  onChanged: (value) => _toggleAvailability(),
                  activeColor: Colors.green,
                ),
                Text(_isAvailable ? 'Available' : 'Unavailable'),
              ],
            ),
            const SizedBox(height: 16),
            
            // Availability Status Card
            Card(
              color: _isAvailable ? Colors.green[50] : Colors.orange[50],
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  children: [
                    Icon(
                      _isAvailable ? Icons.check_circle : Icons.pause_circle,
                      color: _isAvailable ? Colors.green : Colors.orange,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      _isAvailable 
                          ? 'Ready to accept new transport jobs' 
                          : 'Not accepting new jobs at the moment',
                      style: TextStyle(
                        color: _isAvailable ? Colors.green : Colors.orange,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 24),
            const Text(
              'Available Transport Jobs',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            
            _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _availableJobs.isEmpty
                    ? const Card(
                        child: Padding(
                          padding: EdgeInsets.all(32.0),
                          child: Center(
                            child: Text(
                              'No available transport jobs at the moment',
                              style: TextStyle(
                                color: Colors.grey,
                                fontSize: 16,
                              ),
                            ),
                          ),
                        ),
                      )
                    : Column(
                        children: _availableJobs.map((job) {
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            elevation: 2,
                            child: Padding(
                              padding: const EdgeInsets.all(16.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      CircleAvatar(
                                        backgroundColor: Colors.green[100],
                                        child: Text(
                                          job['crop_type'][0].toUpperCase(),
                                          style: const TextStyle(
                                            color: Colors.green,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              '${job['crop_type'][0].toUpperCase()}${job['crop_type'].substring(1)}',
                                              style: const TextStyle(
                                                fontWeight: FontWeight.bold,
                                                fontSize: 16,
                                              ),
                                            ),
                                            Text(
                                              '${job['quantity_kg']} kg',
                                              style: TextStyle(
                                                color: Colors.grey[600],
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 12),
                                  Row(
                                    children: [
                                      const Icon(Icons.location_on, size: 16, color: Colors.grey),
                                      const SizedBox(width: 4),
                                      Expanded(child: Text('From: ${job['pickup_location']}')),
                                    ],
                                  ),
                                  Row(
                                    children: [
                                      const Icon(Icons.place, size: 16, color: Colors.grey),
                                      const SizedBox(width: 4),
                                      Expanded(child: Text('To: ${job['destination']}')),
                                    ],
                                  ),
                                  Row(
                                    children: [
                                      const Icon(Icons.directions_car, size: 16, color: Colors.grey),
                                      const SizedBox(width: 4),
                                      Text('${job['distance_km']} km'),
                                      const Spacer(),
                                      const Icon(Icons.attach_money, size: 16, color: Colors.green),
                                      const SizedBox(width: 4),
                                      Text('\$${job['estimated_fare']}'),
                                    ],
                                  ),
                                  const SizedBox(height: 12),
                                  _isAvailable
                                      ? ElevatedButton(
                                          onPressed: () => _acceptJob(job['id']),
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: Colors.green,
                                            foregroundColor: Colors.white,
                                            minimumSize: const Size(double.infinity, 40),
                                          ),
                                          child: const Text('Accept Job'),
                                        )
                                      : OutlinedButton(
                                          onPressed: null,
                                          style: OutlinedButton.styleFrom(
                                            minimumSize: const Size(double.infinity, 40),
                                          ),
                                          child: const Text('Unavailable'),
                                        ),
                                ],
                              ),
                            ),
                          );
                        }).toList(),
                      ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _loadAvailableJobs,
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        child: const Icon(Icons.refresh),
      ),
    );
  }
}