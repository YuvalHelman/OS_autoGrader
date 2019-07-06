#ifndef CHARDEV_H
#define CHARDEV_H

#include <linux/ioctl.h>

#define MAJOR_NUM 241

#define MAX_SLOT_COUNT 256

#define MIN_MESSAGE_LENGTH 0
#define MAX_MESSAGE_LENGTH 128

#define OVERWRITE_MODE 0
#define APPEND_MODE 1

// Set the message of the device driver
#define MSG_SLOT_CHANNEL _IOW(MAJOR_NUM, 0, unsigned int)
#define MSG_SLOT_WRITE_MODE _IOW(MAJOR_NUM, 1, unsigned int)


#define DEVICE_NAME "message_slot_device"
#define SUCCESS 0

typedef struct messageChannel {
	int channelId;
    char* message;
} messageChannel;
typedef messageChannel *MESSAGE_CHANNEL;

typedef struct node {
	struct node* next;
	MESSAGE_CHANNEL data;
} node;
typedef node *NODE;

typedef struct messageSlot{
	int writeMode;
	MESSAGE_CHANNEL channel;
} messageSlot;
typedef messageSlot *MESSAGE_SLOT;

#endif
