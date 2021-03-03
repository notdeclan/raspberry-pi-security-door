#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/kdev_t.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/delay.h>
#include <linux/uaccess.h>
#include <linux/gpio.h>
#include <linux/interrupt.h>
#include <linux/slab.h>
#include <linux/ioctl.h>
#include <asm/io.h>
#include <linux/printk.h>
#include <linux/kobject.h>
#include <linux/jiffies.h>
#include <linux/sysfs.h>
#include <linux/sched.h>
#include <linux/signal.h>
#include <linux/sched/signal.h>

// Module Functions
static int __init door_init(void);
static void __exit door_exit(void);

/**
 * IOCTL
 */
// Used to Set the Userspace Application for Signalling
#define IOCTL_TASK_SET _IO('a', 0) // _IO = ioctl with no parameters

static int      ioctl_open(struct inode *inode, struct file *file);
static int      ioctl_release(struct inode *inode, struct file *file);
static long     ioctl_interface(struct file *file_p, unsigned int cmd, unsigned long arg);
static ssize_t  ioctl_read(struct file *file_p, char __user *buf, size_t len, loff_t *off);

static struct file_operations fops = {
        .owner          = THIS_MODULE,
        .open           = ioctl_open,
        .release        = ioctl_release,
        .unlocked_ioctl = ioctl_interface,
        .read           = ioctl_read,
};

/**
 * SysFS Functions
 */
static ssize_t          door_state_show(struct kobject * kobj, struct kobj_attribute *attr, char* buf);

// GPIO Structure
typedef struct {
    unsigned pin;
    unsigned long trigger;
    int irq;
    const char* description;
    char last_value;
} GPIO;