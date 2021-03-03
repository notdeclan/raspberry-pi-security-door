#include "driver.h"

// Device Instance Variables
dev_t device_number = 0;
static struct cdev device;
static struct class * device_class;

// Application Signalling
static struct task_struct *task = NULL;

// SysFS
static struct kobject *kobj_ref; // Used to store the sysfs directory
static volatile int            door_state         = 0; // Store door value
static struct kobj_attribute   door_state_attr    = __ATTR_RO(door_state); // creates door_state file

// GPIO
static GPIO sensor   = {21, IRQF_TRIGGER_RISING,  0, "Sensor", 0};

// Debouncing
extern unsigned long volatile jiffies;
unsigned long old_jiffie = 0;

/**
 * Called when the door state sysfs file is read
 */
static ssize_t door_state_show(struct kobject * kobj, struct kobj_attribute *attr, char* buf) {
    pr_info("door_state_show: sysfs read\n");
    return sprintf(buf, "%d\n", door_state);
}


/**
 * Called when there is an interupt on the registered GPIO pins
 */
static irqreturn_t door_irq_handler(int irq, void *dev_id) {
    GPIO* gpio = (GPIO*) dev_id;
    int new_value = gpio_get_value(gpio->pin);

    // If last value was that, skip it
    if(new_value == gpio->last_value)
        return IRQ_HANDLED;

    // Handle Debouncing
    if (jiffies - old_jiffie < 20)
        return IRQ_HANDLED;

    old_jiffie = jiffies;
    gpio->last_value = new_value;
    door_state = new_value;

    pr_info("irq_handler: Interrupt Occurred on GPIO(description=%s, pin=%d, irq=%d)\n", gpio->description, gpio->pin, irq);

    // Send Response Signal
    struct kernel_siginfo info;
    memset(&info, 0, sizeof(struct kernel_siginfo));
    info.si_signo = 10;
    info.si_code = SI_QUEUE;
    info.si_int = 1;

    if (task != NULL) {
        if(send_sig_info(info.si_signo, &info, task) > 0) {
            pr_info("irq_handler: Sent Signal to: Task(pid=%d)\n", task->pid);
            return IRQ_HANDLED;
        }
    }

    pr_err("irq:handler: Failed to send Signal")
    return IRQ_HANDLED;
}


/**
 * Initializes GPIO struct
 */
static int initialize_gpio(GPIO* gpio) {
    pr_info("initialize_gpio: Attempting to initialize GPIO: %s\n", gpio->description);

    if(gpio_request(gpio->pin, gpio->description)) {
        pr_err("initialize_gpio: Failed to request GPIO: %s\n", gpio->description);
        return false;
    }

    pr_info("initialize_gpio: Requested GPIO\n");
    gpio_direction_input(gpio->pin);

    pr_info("initialize_gpio: Set direction input\n");

    if((gpio->irq = gpio_to_irq(gpio->pin)) < 0) {
        pr_err("initialize_gpio: Failed to create interrupt for: %s\n", gpio->description);
        return false;
    }

    if(request_irq(gpio->irq, (irq_handler_t) door_irq_handler, gpio->trigger, gpio->description, gpio)) {
        pr_err("initialize_gpio: Failed to request interrupt handler\n");
        return false;
    }

    pr_info("initialize_gpio: Created interrupt for GPIO(pin=%d, description=%s, irq=%d)\n", gpio->pin, gpio->description, gpio->irq);

    return true;
}

/**
 * Removes interrupt handler and free gpio
 * @param gpio: GPIO struct to release
 */
void release_gpio(GPIO* gpio) {
    free_irq(gpio->irq, gpio);
    gpio_free(gpio->pin);
}

/**
 * Called when the Device file is read
 */
static ssize_t ioctl_read(struct file *file_p, char __user *buf, size_t len, loff_t *off) {
    pr_info("Device File Read\n");
    return 0;
}

/**
 * Called when the Device file is opened
 */
static int ioctl_open(struct inode *inode, struct file *file) {
    pr_info("Device File Opened: %p\n", file);
    return 0;
}


/**
 * Called when the Device File is closed
 */
static int ioctl_release(struct inode *inode, struct file *file) {
    struct task_struct *ref_task = get_current();
    pr_info("Device File Closed: %p\n", file);

    // Delete the Task Signal
    if(ref_task == task) {
        task = NULL;
    }

    return 0;
}

/**
 * Handles IOCTL commands
 */
static long ioctl_interface(struct file *file_p, unsigned int cmd, unsigned long arg) {
    if(cmd == IOCTL_TASK_SET) {
        pr_info("ioctl_interface: IOCTL_TASK_SET");
        task = get_current(); // Provides a way of communicating with user space application
    }
    return 0;
}


/**
 * Module Initialization
 */
static int __init door_init(void) {
    pr_info("door_init: Begin Initialization\n");

    // Dynamically Allocate a device number
    if(alloc_chrdev_region(&device_number, 0, 1, "door_dev") > 0) {
        pr_err("door_init: Failed to allocate Major Number\n");
        goto register_err;
    }

    pr_info("door_init: Registered Device (major=%d, minor=%d)", MAJOR(device_number), MINOR(device_number));

    // Initialize cdev struct
    cdev_init(&device, &fops);

    pr_info("door_init: Initialized cdev struct\n");

    // Add Character Device
    if((cdev_add(&device, device_number, 1)) < 0){
        pr_err("door_init: Failed to add the device to the system\n");
        goto class_err;
    }

    pr_info("door_init: Added character device\n");

    // Create struct class
    if((device_class = class_create(THIS_MODULE, "device_class")) == NULL) {
        pr_err("door_init: Failed to create the struct class\n");
        goto class_err;
    }

    pr_info("door_init: Created struct class\n");

    // Create device
    if((device_create(device_class, NULL, device_number, NULL, "door_device")) == NULL) {
        pr_err("door_init: Failed to create device\n");
        goto device_err;
    }

    pr_info("door_init: Created device class\n");

    // Configure GPIO
    if(initialize_gpio(&sensor) == false) {
        goto sensor_err;
    }

    // Create SysFS Directory (/sys/fs/security_door)
    kobj_ref = kobject_create_and_add("security_door", fs_kobj);

    pr_info("door_init: Created SysFS directory\n");

    // Create SysFS File for Door state (/sys/fs/security_door/door_state)
    if(sysfs_create_file(kobj_ref, &door_state_attr.attr)){
        pr_err("Failed to create sysfs file for Door State\n");
        sysfs_remove_file(fs_kobj, &door_state_attr.attr);
        goto sysfs_err;
    }

    pr_info("door_init: Created SysFS file for Door State\n");

    return 0;

    register_err:
        unregister_chrdev_region(device_number, 1);
    class_err:
        class_destroy(device_class);
    sensor_err:
        release_gpio(&sensor);
    device_err:
        device_destroy(device_class, device_number);
    sysfs_err:
        kobject_put(kobj_ref);
    return -1;
}

/**
 * Module Exit
 */
static void __exit door_exit(void) {
    pr_info("door_exit: Begin Exit\n");

    // Remove SysFS
    kobject_put(kobj_ref);
    sysfs_remove_file(fs_kobj, &door_state_attr.attr);
    pr_info("door_exit: Removed SysFS Attributes\n");

    // Un-export and Free GPIO
    release_gpio(&sensor);
    pr_info("door_exit: Freed GPIO\n");

    // Remove Driver and Device
    device_destroy(device_class, device_number);
    class_destroy(device_class);
    cdev_del(&device);
    pr_info("door_exit: Destroyed Device Class\n");

    // Remove Device Number Allocation
    unregister_chrdev_region(device_number, 1);
    pr_info("door_exit: Removed Device Number Allocation");

    pr_info("door_exit: Device Driver Removed\n");
    return;
}

// Register module entry and exit points
module_init(door_init);
module_exit(door_exit);

// Module Metadata
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Declan Woodham");
MODULE_DESCRIPTION("Security Door Driver");
MODULE_VERSION("1");