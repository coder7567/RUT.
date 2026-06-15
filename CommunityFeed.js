import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  FlatList,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';

/**
 * UI.5 CommunitySocialFeed Screen
 * FlatList renderer utilizing rugged, tactile dark aesthetic.
 */
const CommunityFeed = () => {
  // Mock initial state for community feed items
  const [feedItems, setFeedItems] = useState([
    {
      id: '1',
      type: 'condition_report',
      reporter: 'TrailBreaker_99',
      obstacle_type: 'Deep Mud',
      coordinates: '42.035, -91.602',
      timestamp: '10m ago',
      details: 'Winch strongly recommended. Water depth approx 2.5ft near crossing.',
    },
    {
      id: '2',
      type: 'trail_submission',
      submitter: 'DirtKing_Iowa',
      route_name: 'Marion Level-C Connect',
      upvotes: 14,
      timestamp: '2h ago',
      details: 'Unverified dirt trail linking Marion backroads. Smooth dirt with brief gravel runs.',
      status: 'verified',
    },
    {
      id: '3',
      type: 'condition_report',
      reporter: 'Overland_Wrangler',
      obstacle_type: 'Fallen Tree',
      coordinates: '42.029, -91.590',
      timestamp: '4h ago',
      details: 'Large Oak blocking Level B track. Passable only for narrow motorcycles.',
    }
  ]);

  const handleUpvote = (id) => {
    setFeedItems(prevItems =>
      prevItems.map(item =>
        item.id === id && item.type === 'trail_submission'
          ? { ...item, upvotes: item.upvotes + 1 }
          : item
      )
    );
  };

  const renderItem = ({ item }) => {
    const isReport = item.type === 'condition_report';

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={[styles.badge, isReport ? styles.badgeReport : styles.badgeTrail]}>
            {isReport ? 'HAZARD ALERT' : 'TRAIL SUBMISSION'}
          </Text>
          <Text style={styles.timestamp}>{item.timestamp}</Text>
        </View>

        <Text style={styles.author}>Posted by @{isReport ? item.reporter : item.submitter}</Text>

        {isReport ? (
          <View>
            <Text style={styles.titleText}>{item.obstacle_type}</Text>
            <Text style={styles.coordinateText}>GPS: {item.coordinates}</Text>
          </View>
        ) : (
          <View>
            <Text style={styles.titleText}>{item.route_name}</Text>
            <Text style={styles.verifiedText}>STATUS: {item.status.toUpperCase()}</Text>
          </View>
        )}

        <Text style={styles.detailsText}>{item.details}</Text>

        <View style={styles.cardFooter}>
          {isReport ? (
            <Text style={styles.activeStatus}>Status: ACTIVE HAZARD</Text>
          ) : (
            <TouchableOpacity 
              style={styles.upvoteButton}
              onPress={() => handleUpvote(item.id)}
            >
              <Text style={styles.upvoteText}>👍 UPVOTE ({item.upvotes})</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={feedItems}
        renderItem={renderItem}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.listContent}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  listContent: {
    padding: 16,
  },
  card: {
    backgroundColor: '#1A1A1A',
    borderWidth: 2,
    borderColor: '#2C2C2C',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  badge: {
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    overflow: 'hidden',
  },
  badgeReport: {
    backgroundColor: '#FF3333',
    color: '#FFFFFF',
  },
  badgeTrail: {
    backgroundColor: '#00FF66',
    color: '#000000',
  },
  timestamp: {
    color: '#888888',
    fontSize: 11,
  },
  author: {
    color: '#888888',
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  titleText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '900',
    marginBottom: 4,
  },
  coordinateText: {
    color: '#00E5FF',
    fontFamily: 'monospace',
    fontSize: 12,
    marginBottom: 8,
  },
  verifiedText: {
    color: '#00FF66',
    fontWeight: 'bold',
    fontSize: 12,
    marginBottom: 8,
  },
  detailsText: {
    color: '#DDDDDD',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  cardFooter: {
    borderTopWidth: 1,
    borderTopColor: '#2C2C2C',
    paddingTop: 12,
    flexDirection: 'row',
    justifyContent: 'flex-start',
  },
  activeStatus: {
    color: '#FF3333',
    fontWeight: 'bold',
    fontSize: 12,
  },
  upvoteButton: {
    backgroundColor: '#222222',
    borderWidth: 1,
    borderColor: '#00FF66',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 4,
  },
  upvoteText: {
    color: '#00FF66',
    fontWeight: 'bold',
    fontSize: 11,
  },
});

export default CommunityFeed;
