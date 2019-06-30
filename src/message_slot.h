#ifndef MESSAGE_SLOT_H
#define MESSAGE_SLOT_H

#include <linux/ioctl.h>

#define MAJOR_NUM 50

// Set the message of the device driver
#define MSG_SLOT_WRITE_MODE _IOW(MAJOR_NUM, 0, unsigned long)
#define MSG_SLOT_CHANNEL _IOW(MAJOR_NUM, 1, unsigned long)

#define DEVICE_RANGE_NAME "message_slot"
#define BUF_LEN 128
#define SLOTS_LEN 255
#define SUCCESS 0

#define OVERWRITE_MODE 0
#define APPEND_MODE 1

#endif
