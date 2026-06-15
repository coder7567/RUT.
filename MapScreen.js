import React, { useState, useEffect, useRef } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import MapView, { Polyline, Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import Slider from '@react-native-community/slider';
import * as Location from 'expo-location';
import { getRoute, triggerBailout, triggerEmergencyBeacon } from '../services/api';
import HazardReportModal from '../components/HazardReportModal';
import ConvoyOverlay from '../components/ConvoyOverlay';

/**
 * UI.3, UI.8 & UI.12 MapScreen Component
 * Marion, Iowa coordinate focus. Uses high-contrast, tactile rugged UI guidelines.
 * Integrated with HazardReportModal, ConvoyOverlay, and satellite SOS triggers.
 */
const MapScreen = () => {
  const [loading, setLoading] = useState(false);
  const [unorthodoxyScore, setUnorthodoxyScore] = useState(0.5);
  const [routeCoords, setRouteCoords] = useState([]);
  const [bailoutCoords, setBailoutCoords] = useState([]);
  const [hazardModalVisible, setHazardModalVisible] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [isTransitActive, setIsTransitActive] = useState(false);
  
  const routeRequested = useRef(false);
  
  // Marion, Iowa center coordinate setup for testing
  const initialRegion = {
    latitude: 42.033,
    longitude: -91.598,
    latitudeDelta: 0.052,
    longitudeDelta: 0.052,
  };

  const [startCoord, setStartCoord] = useState([-91.666, 41.978]);
  const [endCoord, setEndCoord] = useState([-92.3587, 42.4995]);
  const [mapCenter, setMapCenter] = useState(initialRegion);

  useEffect(() => {
    const requestLocationPermission = async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert(
            'Location Permission Denied',
            'Foreground location access is required to track your device in real-time. Please enable it in system settings.'
          );
          return;
        }

        const location = await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.High,
        });
        setUserLocation(location.coords);
      } catch (err) {
        Alert.alert(
          'Location Tracking Error',
          'Failed to retrieve dynamic GPS position. Ensure location services are active.'
        );
      }
    };

    requestLocationPermission();
  }, []);

  const fetchRUTRoute = async () => {
    routeRequested.current = true;
    setLoading(true);
    setBailoutCoords([]); // Clear existing bailout overlays
    try {
      const data = await getRoute(startCoord, endCoord, unorthodoxyScore);
      if (data.status === 'success' && data.coordinates) {
        // Convert [lon, lat] list from API to {latitude, longitude} for react-native-maps
        const mapped = data.coordinates.map(c => ({
          longitude: c[0],
          latitude: c[1],
        }));
        setRouteCoords(mapped);
        setIsTransitActive(true);
      }
    } catch (err) {
      Alert.alert('Routing Error', 'Could not generate RUT path. Ensure backend server is active.');
    } finally {
      setLoading(false);
    }
  };

  const cancelRoute = () => {
    setRouteCoords([]);
    setBailoutCoords([]);
    setIsTransitActive(false);
  };

  const runBailout = async () => {
    if (!userLocation) {
      Alert.alert(
        'Satellite Lock Pending',
        'Please wait for a clear satellite GPS lock before triggering a bailout route.'
      );
      return;
    }
    setLoading(true);
    setRouteCoords([]); // Clear current routing overlay
    const currentLoc = [userLocation.longitude, userLocation.latitude];
    try {
      const data = await triggerBailout(currentLoc);
      if (data.status === 'success' && data.coordinates) {
        if (data.coordinates.length <= 1) {
          Alert.alert('Bail Out Success', 'You are already on a paved road.');
          return;
        }
        const mapped = data.coordinates.map(c => ({
          longitude: c[0],
          latitude: c[1],
        }));
        setBailoutCoords(mapped);
        Alert.alert('Bail Out Active', 'Escape route to nearest paved highway plotted in red.');
      }
    } catch (err) {
      Alert.alert('Bail Out Error', 'Unable to calculate escape path.');
    } finally {
      setLoading(false);
    }
  };

  const sendEmergencySOS = () => {
    Alert.alert(
      'TRANSMIT SOS BEACON',
      'Are you sure? This will compile and transmit an offline distress packet over simulated satellite link.',
      [
        { text: 'CANCEL', style: 'cancel' },
        { 
          text: 'CONFIRM SOS', 
          style: 'destructive',
          onPress: async () => {
            setLoading(true);
            try {
              // Set userId as the string token matching active convoy session
              const result = await triggerEmergencyBeacon('User-1', initialRegion.latitude, initialRegion.longitude, 'CRITICAL SOS');
              if (result.status === 'SOS_BROADCAST_SENT') {
                Alert.alert('SOS Transmitted', `Distress packet successfully compiled: ${result.raw_packet}`);
              }
            } catch (err) {
              Alert.alert('SOS Delivery Failure', 'Satellite connection simulation failed. Verify backend.');
            } finally {
              setLoading(false);
            }
          }
        }
      ]
    );
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (routeRequested.current) {
      fetchRUTRoute();
    }
  }, [unorthodoxyScore]);

  return (
    <View style={styles.container}>
      <MapView
        provider={PROVIDER_GOOGLE}
        style={styles.map}
        initialRegion={initialRegion}
        customMapStyle={darkMapStyle}
        onRegionChangeComplete={(region) => {
          setMapCenter(region);
        }}
      >
        {/* User Current Location Marker */}
        {userLocation && (
          <Marker
            coordinate={{
              latitude: userLocation.latitude,
              longitude: userLocation.longitude,
            }}
            title="Current Location"
          >
            <View style={styles.userLocationMarker} />
          </Marker>
        )}
        {/* Render primary route path (Green) */}
        {routeCoords.length > 0 && (
          <Polyline
            coordinates={routeCoords}
            strokeColor="#00FF66"
            strokeWidth={5}
          />
        )}

        {/* Render bailout emergency path (Red) */}
        {bailoutCoords.length > 0 && (
          <Polyline
            coordinates={bailoutCoords}
            strokeColor="#FF3333"
            strokeWidth={6}
            lineDashPattern={[5, 5]}
          />
        )}

        {/* Start Point Marker */}
        <Marker 
          draggable={!isTransitActive}
          coordinate={{ latitude: startCoord[1], longitude: startCoord[0] }} 
          title="Start" 
          pinColor="#00FF66"
          onDragEnd={(e) => {
            const { latitude, longitude } = e.nativeEvent.coordinate;
            setStartCoord([longitude, latitude]);
          }}
        />

        {/* End Point Marker */}
        <Marker 
          draggable={!isTransitActive}
          coordinate={{ latitude: endCoord[1], longitude: endCoord[0] }} 
          title="Destination" 
          pinColor="#00E5FF"
          onDragEnd={(e) => {
            const { latitude, longitude } = e.nativeEvent.coordinate;
            setEndCoord([longitude, latitude]);
          }}
        />
      </MapView>

      {/* Center-Screen Target Reticle */}
      <View style={styles.reticleContainer} pointerEvents="none">
        <View style={styles.reticleCrosshairHorizontal} />
        <View style={styles.reticleCrosshairVertical} />
        <View style={styles.reticleDot} />
      </View>

      {/* UI.12 Convoy Overlay Radar UI */}
      <ConvoyOverlay />

      <SafeAreaView style={styles.overlayContainer}>
        {/* Top Panel: Shortcut Slider */}
        <View style={styles.topPanel}>
          <Text style={styles.panelTitle}>RUT UNORTHODOXY SLIDER</Text>
          <View style={styles.sliderRow}>
            <Text style={styles.sliderLabel}>PAVED</Text>
            <Slider
              style={styles.slider}
              minimumValue={0.0}
              maximumValue={1.0}
              value={unorthodoxyScore}
              minimumTrackTintColor="#00FF66"
              maximumTrackTintColor="#555555"
              thumbTintColor="#00FF66"
              onSlidingComplete={(val) => setUnorthodoxyScore(parseFloat(val.toFixed(2)))}
            />
            <Text style={styles.sliderLabel}>RUT</Text>
          </View>
          <Text style={styles.valueIndicator}>Score: {unorthodoxyScore.toFixed(2)}</Text>
        </View>

        {loading && (
          <View style={styles.loader}>
            <ActivityIndicator size="large" color="#00FF66" />
          </View>
        )}

        {/* Bottom Panel: Tactical Triggers */}
        <View style={styles.bottomPanel}>
          {!isTransitActive ? (
            <>
              {/* Row 1: LOCK START / DESTINATION */}
              <View style={styles.planningRow}>
                <TouchableOpacity 
                  style={styles.planningLockButton}
                  activeOpacity={0.8}
                  onPress={() => {
                    if (mapCenter) {
                      setStartCoord([mapCenter.longitude, mapCenter.latitude]);
                    }
                  }}
                >
                  <Text style={styles.planningLockText}>LOCK START</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.planningLockButton}
                  activeOpacity={0.8}
                  onPress={() => {
                    if (mapCenter) {
                      setEndCoord([mapCenter.longitude, mapCenter.latitude]);
                    }
                  }}
                >
                  <Text style={styles.planningLockText}>LOCK DESTINATION</Text>
                </TouchableOpacity>
              </View>

              {/* Row 2: ENGAGE DRIVE (Ignition Switch) */}
              <TouchableOpacity 
                style={[
                  styles.engageButton,
                  loading ? styles.engageButtonDisabled : styles.engageButtonEnabled
                ]} 
                activeOpacity={0.8}
                disabled={loading}
                onPress={fetchRUTRoute}
              >
                <Text style={[styles.engageButtonText, loading && styles.engageButtonTextDisabled]}>ENGAGE DRIVE</Text>
                <Text style={[styles.engageButtonSubText, loading && styles.engageButtonSubTextDisabled]}>// COGNITIVE ROUTING OVERRIDE</Text>
              </TouchableOpacity>
            </>
          ) : (
            <>
              {/* Row 1: REPORT HAZARD, BAIL OUT, SOS BEACON */}
              <View style={styles.transitRow}>
                <TouchableOpacity 
                  style={styles.transitButtonHazard} 
                  activeOpacity={0.8}
                  onPress={() => setHazardModalVisible(true)}
                >
                  <Text style={[styles.transitButtonText, { color: '#000000' }]}>REPORT HAZARD</Text>
                </TouchableOpacity>

                <TouchableOpacity 
                  style={styles.transitButtonBailout} 
                  activeOpacity={0.8}
                  onPress={runBailout}
                >
                  <Text style={[styles.transitButtonText, { color: '#FFFFFF' }]}>BAIL OUT</Text>
                </TouchableOpacity>

                <TouchableOpacity 
                  style={styles.transitButtonSos} 
                  activeOpacity={0.8}
                  onPress={sendEmergencySOS}
                >
                  <Text style={[styles.transitButtonText, { color: '#FF3333' }]}>SOS BEACON</Text>
                </TouchableOpacity>
              </View>

              {/* Row 2: CANCEL MISSION // RESET PLAN */}
              <TouchableOpacity 
                style={styles.cancelMissionButton} 
                activeOpacity={0.8}
                onPress={cancelRoute}
              >
                <Text style={styles.cancelMissionButtonText}>CANCEL MISSION // RESET PLAN</Text>
              </TouchableOpacity>
            </>
          )}
        </View>
      </SafeAreaView>

      {/* Active Hazard Modal Ingestion */}
      <HazardReportModal
        visible={hazardModalVisible}
        onClose={() => setHazardModalVisible(false)}
        latitude={initialRegion.latitude}
        longitude={initialRegion.longitude}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
  },
  map: {
    ...StyleSheet.absoluteFillObject,
  },
  userLocationMarker: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: '#006622',
    borderWidth: 2,
    borderColor: '#FFFFFF',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.8,
    shadowRadius: 3,
    elevation: 5,
  },
  overlayContainer: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'space-between',
    pointerEvents: 'box-none',
  },
  topPanel: {
    backgroundColor: 'rgba(20, 20, 20, 0.95)',
    borderWidth: 2,
    borderColor: '#333333',
    margin: 16,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  panelTitle: {
    color: '#00FF66',
    fontWeight: 'bold',
    fontSize: 14,
    letterSpacing: 1.5,
    marginBottom: 12,
  },
  sliderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
  },
  sliderLabel: {
    color: '#888888',
    fontSize: 10,
    fontWeight: 'bold',
    width: 45,
    textAlign: 'center',
  },
  slider: {
    flex: 1,
    height: 40,
  },
  valueIndicator: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
    marginTop: 4,
  },
  loader: {
    alignSelf: 'center',
    backgroundColor: 'rgba(0,0,0,0.8)',
    padding: 16,
    borderRadius: 8,
  },
  bottomPanel: {
    margin: 16,
    pointerEvents: 'auto',
  },
  reticleContainer: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
  },
  reticleCrosshairHorizontal: {
    position: 'absolute',
    width: 30,
    height: 2,
    backgroundColor: '#00FF66',
    opacity: 0.8,
  },
  reticleCrosshairVertical: {
    position: 'absolute',
    width: 2,
    height: 30,
    backgroundColor: '#00FF66',
    opacity: 0.8,
  },
  reticleDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#00FF66',
  },
  planningRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    width: '100%',
  },
  planningLockButton: {
    width: '48%',
    backgroundColor: 'rgba(20, 20, 20, 0.95)',
    borderWidth: 2,
    borderColor: '#00FF66',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.5,
    shadowRadius: 3,
    elevation: 5,
  },
  planningLockText: {
    color: '#00FF66',
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 1.5,
  },
  engageButton: {
    width: '100%',
    borderWidth: 3,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 5,
    elevation: 8,
  },
  engageButtonEnabled: {
    backgroundColor: '#00FF66',
    borderColor: '#FFFFFF',
  },
  engageButtonDisabled: {
    backgroundColor: '#444444',
    borderColor: '#444444',
    opacity: 0.6,
    shadowOpacity: 0,
    elevation: 0,
  },
  engageButtonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: 2,
  },
  engageButtonTextDisabled: {
    color: '#888888',
  },
  engageButtonSubText: {
    color: '#000000',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1.5,
    marginTop: 1,
  },
  engageButtonSubTextDisabled: {
    color: '#888888',
  },
  transitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    width: '100%',
  },
  transitButtonHazard: {
    width: '31%',
    backgroundColor: '#FFCC00',
    borderWidth: 2,
    borderColor: '#FFFFFF',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.5,
    shadowRadius: 3,
    elevation: 5,
  },
  transitButtonBailout: {
    width: '31%',
    backgroundColor: '#FF3333',
    borderWidth: 2,
    borderColor: '#FFFFFF',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.5,
    shadowRadius: 3,
    elevation: 5,
  },
  transitButtonSos: {
    width: '31%',
    backgroundColor: '#000000',
    borderWidth: 2,
    borderColor: '#FF3333',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.5,
    shadowRadius: 3,
    elevation: 5,
  },
  transitButtonText: {
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.5,
    textAlign: 'center',
  },
  cancelMissionButton: {
    width: '100%',
    backgroundColor: 'rgba(20, 20, 20, 0.95)',
    borderWidth: 2,
    borderColor: '#5a3b3b',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.5,
    shadowRadius: 3,
    elevation: 5,
  },
  cancelMissionButtonText: {
    color: '#cc6666',
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 2,
  },
});

// Custom dark high-contrast map tiles styling vector json
const darkMapStyle = [
  { "elementType": "geometry", "stylers": [{ "color": "#1a1a1a" }] },
  { "elementType": "labels.text.fill", "stylers": [{ "color": "#747474" }] },
  { "elementType": "labels.text.stroke", "stylers": [{ "color": "#1a1a1a" }] },
  { "featureType": "administrative", "elementType": "geometry", "stylers": [{ "visibility": "off" }] },
  { "featureType": "landscape", "elementType": "geometry.fill", "stylers": [{ "color": "#121212" }] },
  { "featureType": "road", "elementType": "geometry.fill", "stylers": [{ "color": "#2c2c2c" }] },
  { "featureType": "road.highway", "elementType": "geometry.fill", "stylers": [{ "color": "#3c3c3c" }] },
  { "featureType": "water", "elementType": "geometry", "stylers": [{ "color": "#0d1b2a" }] }
];

export default MapScreen;
