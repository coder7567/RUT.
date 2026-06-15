import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  Switch,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Alert,
} from 'react-native';
import Slider from '@react-native-community/slider';

/**
 * UI.7 Settings & Vehicle Profile Screen
 * Provides tactile configuration panels to align route verification against hardware limits.
 */
const SettingsScreen = () => {
  const [vehicleName, setVehicleName] = useState('Jeep Wrangler Rubicon');
  const [clearanceLevel, setClearanceLevel] = useState(3);
  const [hasWinch, setHasWinch] = useState(true);
  const [hasTowStraps, setHasTowStraps] = useState(true);
  const [hasSnorkel, setHasSnorkel] = useState(false);

  const handleSaveProfile = () => {
    // In a production configuration, this sends a payload to /api/vehicles
    const profilePayload = {
      vehicle_name: vehicleName,
      clearance_level: clearanceLevel,
      has_winch: hasWinch,
      has_tow_straps: hasTowStraps,
      has_snorkel: hasSnorkel,
    };
    
    console.log('Saving vehicle profile payload:', profilePayload);
    Alert.alert(
      'Profile Saved',
      'Your vehicle specifications have been successfully synced to your local route safety checker.'
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.sectionTitle}>VEHICLE SPECIFICATIONS</Text>
        
        <View style={styles.inputCard}>
          <Text style={styles.inputLabel}>VEHICLE NAME / BUILD</Text>
          <TextInput
            style={styles.textInput}
            value={vehicleName}
            onChangeText={setVehicleName}
            placeholder="e.g. Toyota Tacoma 4x4"
            placeholderTextColor="#666666"
          />
        </View>

        <View style={styles.inputCard}>
          <Text style={styles.inputLabel}>SUSPENSION CLEARANCE LEVEL: {clearanceLevel}</Text>
          <View style={styles.sliderRow}>
            <Text style={styles.sliderBound}>STOCK (1)</Text>
            <Slider
              style={styles.slider}
              minimumValue={1}
              maximumValue={5}
              step={1}
              value={clearanceLevel}
              minimumTrackTintColor="#00FF66"
              maximumTrackTintColor="#333333"
              thumbTintColor="#00FF66"
              onValueChange={(val) => setClearanceLevel(val)}
            />
            <Text style={styles.sliderBound}>LIFTED (5)</Text>
          </View>
        </View>

        <Text style={styles.sectionTitle}>RECOVERY & DEEP WATER GEAR</Text>

        <View style={styles.toggleCard}>
          <View style={styles.toggleRow}>
            <View>
              <Text style={styles.toggleLabel}>RECOVERY WINCH</Text>
              <Text style={styles.toggleSublabel}>Recommended for Level C trails</Text>
            </View>
            <Switch
              value={hasWinch}
              onValueChange={setHasWinch}
              trackColor={{ false: '#333333', true: 'rgba(0, 255, 102, 0.4)' }}
              thumbColor={hasWinch ? '#00FF66' : '#888888'}
            />
          </View>
        </View>

        <View style={styles.toggleCard}>
          <View style={styles.toggleRow}>
            <View>
              <Text style={styles.toggleLabel}>HEAVY TOW STRAPS</Text>
              <Text style={styles.toggleSublabel}>Required for group convoy runs</Text>
            </View>
            <Switch
              value={hasTowStraps}
              onValueChange={setHasTowStraps}
              trackColor={{ false: '#333333', true: 'rgba(0, 255, 102, 0.4)' }}
              thumbColor={hasTowStraps ? '#00FF66' : '#888888'}
            />
          </View>
        </View>

        <View style={styles.toggleCard}>
          <View style={styles.toggleRow}>
            <View>
              <Text style={styles.toggleLabel}>ENGINE SNORKEL</Text>
              <Text style={styles.toggleSublabel}>Mandatory for flooded crossings</Text>
            </View>
            <Switch
              value={hasSnorkel}
              onValueChange={setHasSnorkel}
              trackColor={{ false: '#333333', true: 'rgba(0, 255, 102, 0.4)' }}
              thumbColor={hasSnorkel ? '#00FF66' : '#888888'}
            />
          </View>
        </View>

        <TouchableOpacity 
          style={styles.saveButton}
          activeOpacity={0.8}
          onPress={handleSaveProfile}
        >
          <Text style={styles.saveButtonText}>SAVE VEHICLE PROFILE</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  scrollContent: {
    padding: 16,
  },
  sectionTitle: {
    color: '#00FF66',
    fontWeight: '900',
    fontSize: 12,
    letterSpacing: 2,
    marginTop: 16,
    marginBottom: 12,
  },
  inputCard: {
    backgroundColor: '#1A1A1A',
    borderWidth: 2,
    borderColor: '#2C2C2C',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  inputLabel: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 10,
    letterSpacing: 1,
  },
  textInput: {
    backgroundColor: '#222222',
    borderWidth: 1,
    borderColor: '#444444',
    borderRadius: 4,
    color: '#FFFFFF',
    padding: 10,
    fontSize: 14,
    fontWeight: 'bold',
  },
  sliderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sliderBound: {
    color: '#888888',
    fontSize: 10,
    fontWeight: 'bold',
  },
  slider: {
    flex: 1,
    height: 40,
    marginHorizontal: 10,
  },
  toggleCard: {
    backgroundColor: '#1A1A1A',
    borderWidth: 2,
    borderColor: '#2C2C2C',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  toggleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  toggleLabel: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 14,
    letterSpacing: 1,
    marginBottom: 4,
  },
  toggleSublabel: {
    color: '#888888',
    fontSize: 11,
  },
  saveButton: {
    backgroundColor: '#00FF66',
    borderWidth: 2,
    borderColor: '#FFFFFF',
    borderRadius: 8,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 24,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 5,
    elevation: 6,
  },
  saveButtonText: {
    color: '#000000',
    fontWeight: '900',
    fontSize: 16,
    letterSpacing: 1.5,
  },
});

export default SettingsScreen;
