class TransportJob {
  final int? id;
  final FarmerRequest farmerRequest;
  final TransporterProfile? transporter;
  final String status;
  final String? estimatedArrival;
  final Map<String, dynamic>? routeOptimization;
  final double? spoilageRisk;
  final String? createdAt;

  TransportJob({
    this.id,
    required this.farmerRequest,
    this.transporter,
    required this.status,
    this.estimatedArrival,
    this.routeOptimization,
    this.spoilageRisk,
    this.createdAt,
  });

  factory TransportJob.fromJson(Map<String, dynamic> json) {
    return TransportJob(
      id: json['id'],
      farmerRequest: FarmerRequest.fromJson(json['farmer_request']),
      transporter: json['transporter'] != null 
          ? TransporterProfile.fromJson(json['transporter']) 
          : null,
      status: json['status'],
      estimatedArrival: json['estimated_arrival'],
      routeOptimization: json['route_optimization'],
      spoilageRisk: json['spoilage_risk']?.toDouble(),
      createdAt: json['created_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'farmer_request': farmerRequest.toJson(),
      'transporter': transporter?.toJson(),
      'status': status,
      'estimated_arrival': estimatedArrival,
      'route_optimization': routeOptimization,
      'spoilage_risk': spoilageRisk,
      'created_at': createdAt,
    };
  }
}

class FarmerRequest {
  final String cropType;
  final double quantityKg;
  final String location;
  final String destinationMarket;
  final String? preferredDeliveryTime;

  FarmerRequest({
    required this.cropType,
    required this.quantityKg,
    required this.location,
    required this.destinationMarket,
    this.preferredDeliveryTime,
  });

  factory FarmerRequest.fromJson(Map<String, dynamic> json) {
    return FarmerRequest(
      cropType: json['crop_type'],
      quantityKg: json['quantity_kg'].toDouble(),
      location: json['location'],
      destinationMarket: json['destination_market'],
      preferredDeliveryTime: json['preferred_delivery_time'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'crop_type': cropType,
      'quantity_kg': quantityKg,
      'location': location,
      'destination_market': destinationMarket,
      'preferred_delivery_time': preferredDeliveryTime,
    };
  }
}

class TransporterProfile {
  final String vehicleType;
  final double capacityKg;
  final String currentLocation;
  final bool availability;
  final String contactInfo;

  TransporterProfile({
    required this.vehicleType,
    required this.capacityKg,
    required this.currentLocation,
    required this.availability,
    required this.contactInfo,
  });

  factory TransporterProfile.fromJson(Map<String, dynamic> json) {
    return TransporterProfile(
      vehicleType: json['vehicle_type'],
      capacityKg: json['capacity_kg'].toDouble(),
      currentLocation: json['current_location'],
      availability: json['availability'],
      contactInfo: json['contact_info'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'vehicle_type': vehicleType,
      'capacity_kg': capacityKg,
      'current_location': currentLocation,
      'availability': availability,
      'contact_info': contactInfo,
    };
  }
}