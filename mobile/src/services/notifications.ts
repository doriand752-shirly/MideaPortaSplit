import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

import type { ActionableOffer } from '../types';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export async function requestNotificationPermissions(): Promise<boolean> {
  const { status: existing } = await Notifications.getPermissionsAsync();
  if (existing === 'granted') return true;

  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== 'granted') return false;

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('portasplit', {
      name: 'PortaSplit',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
    });
  }

  return true;
}

export async function notifyOffers(offers: ActionableOffer[]): Promise<void> {
  for (const offer of offers) {
    await Notifications.scheduleNotificationAsync({
      content: {
        title:
          offer.kind === 'magasin'
            ? 'PortaSplit — retrait magasin'
            : 'PortaSplit — livraison dispo',
        body: `${offer.title}\n${offer.detail}`,
        data: { url: offer.url },
        sound: true,
      },
      trigger: null,
    });
  }
}

export async function notifyTest(postalCode: string, actionableCount: number): Promise<void> {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: 'PortaSplit — test OK',
      body:
        actionableCount > 0
          ? `${actionableCount} offre(s) actionnable(s) autour de ${postalCode}`
          : `Surveillance active pour ${postalCode}`,
      sound: true,
    },
    trigger: null,
  });
}
