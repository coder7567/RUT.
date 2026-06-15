import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  Modal,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { submitConditionReport } from '../services/api';

/**
 * UI.6 HazardReportModal Component
 * Tactical sliding modal interface allowing rapid, glove-friendly hazard submissions.
 */
const HazardReportModal = ({ visible, onClose, latitude, longitude }) => {
  const [loading, setLoading] = useState(false);
  const [selectedObstacle, setSelectedObstacle] = useState(null);

  const obstacleTypes = [
    'Gate Locked',
    'Washed Out',
    'Deep Mud',
    'Fallen Tree',
    'Flooded Crossing'
  ];

  const handleSubmit = async () => {
    if (!selectedObstacle) {
      Alert.alert('Selection Required', 'Please select an obstacle type before submitting.');
      return;
    }

    setLoading(true);
    try {
      // Mocking reporterId = 1 for MVP testing
      const result = await submitConditionReport({
        reporterId: 1,
        obstacleType: selectedObstacle,
        latitude: latitude || 42.033,
        longitude: longitude || -91.598,
      });

      if (result.status === 'success') {
        Alert.alert('Report Registered', `Successfully filed hazard: ${selectedObstacle}`);
        setSelectedObstacle(null);
        onClose();
      }
    } catch (err) {
      Alert.alert('Submission Failed', 'API server unreachable. Unable to record report.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      animationType="slide"
      transparent={true}
      visible={visible}
      onRequestClose={onClose}
    >
      <View style={styles.modalBackdrop}>
        <View style={styles.modalContent}>
          <Text style={styles.modalHeader}>REPORT ROUTE OBSTACLE</Text>
          
          <Text style={styles.coordLabel}>
            Target: {latitude?.toFixed(5) || '42.03300'}, {longitude?.toFixed(5) || '-91.59800'}
          </Text>

          <View style={styles.gridContainer}>
            {obstacleTypes.map((type) => {
              const isSelected = selectedObstacle === type;
              return (
                <TouchableOpacity
                  key={type}
                  style={[styles.gridItem, isSelected && styles.selectedGridItem]}
                  activeOpacity={0.7}
                  onPress={() => setSelectedObstacle(type)}
                >
                  <Text style={[styles.gridItemText, isSelected && styles.selectedGridItemText]}>
                    {type.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {loading ? (
            <ActivityIndicator size="large" color="#00FF66" style={{ marginVertical: 20 }} />
          ) : (
            <View style={styles.actionContainer}>
              <TouchableOpacity 
                style={[styles.actionButton, styles.submitButton]} 
                onPress={handleSubmit}
              >
                <Text style={styles.submitButtonText}>SUBMIT REPORT</Text>
              </TouchableOpacity>

              <TouchableOpacity 
                style={[styles.actionButton, styles.cancelButton]} 
                onPress={onClose}
              >
                <Text style={styles.cancelButtonText}>CANCEL</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#121212',
    borderTopWidth: 3,
    borderTopColor: '#FF3333',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: 24,
  },
  modalHeader: {
    color: '#FF3333',
    fontWeight: '900',
    fontSize: 16,
    letterSpacing: 2,
    textAlign: 'center',
    marginBottom: 4,
  },
  coordLabel: {
    color: '#888888',
    fontSize: 11,
    textAlign: 'center',
    fontFamily: 'monospace',
    marginBottom: 16,
  },
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  gridItem: {
    backgroundColor: '#1A1A1A',
    borderWidth: 2,
    borderColor: '#333333',
    borderRadius: 8,
    width: '48%',
    height: 60,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    paddingHorizontal: 8,
  },
  selectedGridItem: {
    backgroundColor: 'rgba(255, 51, 51, 0.2)',
    borderColor: '#FF3333',
  },
  gridItemText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 11,
    textAlign: 'center',
    letterSpacing: 0.5,
  },
  selectedGridItemText: {
    color: '#FF3333',
  },
  actionContainer: {
    flexDirection: 'column',
    width: '100%',
  },
  actionButton: {
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 10,
  },
  submitButton: {
    backgroundColor: '#FF3333',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 14,
    letterSpacing: 1.5,
  },
  cancelButton: {
    backgroundColor: '#222222',
    borderWidth: 1,
    borderColor: '#444444',
  },
  cancelButtonText: {
    color: '#888888',
    fontWeight: 'bold',
    fontSize: 12,
  },
});

export default HazardReportModal;
