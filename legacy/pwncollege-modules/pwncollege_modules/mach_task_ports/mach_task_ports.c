{% extends "mac_base/mac_base.c" %}

{% block includes %}
  #include <mach/mach_param.h>
  typedef struct {
     mach_msg_header_t header;
     uint64 body_message;
     mach_msg_trailer_t trailer;
  } message_t;

  typedef struct {
     mach_msg_header_t header;
     mach_msg_size_t descriptor_count;
     mach_msg_ool_ports_descriptor_t descriptor; // This hasn't been used yet, it'll be fun for them to use it 
  } send_port_message_t;

  typedef struct {
     mach_msg_header_t header;
     mach_msg_body_t body;
     mach_msg_port_descriptor_t port_descriptor;
  } send_inline_port_message_t;


{% if challenge.get_flag_function %}
void get_flag(char* buf, uint64 size)
{
    int flag_fd;
    int flag_length;
    flag_fd = open("/flag", 0);
    if (flag_fd < 0) {
        printf("\n  ERROR: Failed to open the flag -- %s!\n", strerror(errno));
        if (geteuid() != 0) {
            printf("  Your effective user id is not 0!\n");
            printf("  You must directly run the suid binary in order to have the correct permissions!\n");
        }
        strncpy(buf, "fake-flag-unable-to-open-flag-file", size-1);
        buf[size-1] = 0;         
    }
    flag_length = read(flag_fd, buf, size);
    if (flag_length <= 0) {
        printf("\n  ERROR: Failed to read the flag -- %s!\n", strerror(errno));
        strncpy(buf, "fake-flag-unable-to-open-flag-file", size-1);
        buf[size-1] = 0;
    }
}
{% endif %}

{% endblock %}

{% block main %}
{

   {% if challenge.get_flag_function %}
       char* flag = malloc(0x1000);
       get_flag(flag, 0x1000-1);
   {% endif %}

   {% if challenge.leak_flag_address %}
       printf("[LEAK] flag is at: %p\n", flag);
   {% endif %}

   {% if challenge.leak_win_variable %}
       int win = -1;
       printf("[LEAK] win is at: %p\n", &win);
   {% endif %}
   
   mach_port_t receive_port;
   kern_return_t kr = mach_port_allocate(mach_task_self(), MACH_PORT_RIGHT_RECEIVE, &receive_port);
   if (kr != KERN_SUCCESS) {
      printf("mach_port_allocate() failed with code 0x%x\n", kr);
      return 1;
   } 

   kr = mach_port_insert_right(mach_task_self(), receive_port, receive_port, MACH_MSG_TYPE_MAKE_SEND);
   if (kr != KERN_SUCCESS) {
      return 1;
   }

   kr = bootstrap_register(bootstrap_port, "{{ challenge.our_register_port_name }}", receive_port);
   if (kr != KERN_SUCCESS) {
      printf("bootstrap_register() failed with code 0x%x\n", kr);
      return 1;
   }

   message_t msg = {};

   // read in the message
   kr = mach_msg(
      &msg.header,  
      MACH_RCV_MSG,     
      0,                
      sizeof(msg),  
      receive_port,
      MACH_MSG_TIMEOUT_NONE,
      MACH_PORT_NULL
      );

   if (kr != KERN_SUCCESS) {
      printf("mach_msg() failed with code 0x%x\n", kr);
      return 1;
   }


   mach_port_t to_reply = msg.header.msgh_remote_port;

   mach_port_t to_send[TASK_MAX_EXCEPTION_PORT_COUNT];
   int num_to_send = -1;

   {% if challenge.give_task_port %}
       to_send[0] = mach_task_self();
       num_to_send = 1;
   {% elif challenge.give_host_priv_port %}
       kr = host_get_host_priv_port(mach_host_self(), &to_send[0]);
       if (kr != KERN_SUCCESS) {
          fprintf(stderr, "Error: Unable to obtain host_priv port. Error code: 0x%x\n", kr);
          return 1;
       }
       num_to_send = 1;
   {% elif challenge.give_task_exception_port %}
       mach_port_t exception_port;
       kr = mach_port_allocate(mach_task_self(), MACH_PORT_RIGHT_RECEIVE, &exception_port);
       if (kr != KERN_SUCCESS) {
          fprintf(stderr, "Error: Unable to allocate a new port. Error code: 0x%x\n", kr);
          return 1;
       }

        kr = mach_port_insert_right(mach_task_self(), exception_port, exception_port, MACH_MSG_TYPE_MAKE_SEND);
        if (kr != KERN_SUCCESS)
        {
            return 1;
        }


        kr = task_set_exception_ports(mach_task_self(), EXC_MASK_ALL, exception_port, EXCEPTION_DEFAULT, THREAD_STATE_NONE);
        if (kr != KERN_SUCCESS)
        {
           fprintf(stderr, "Error: Unable to set exception port. Error code: 0x%x\n", kr);
           return 1;
        }

       
       to_send[0] = exception_port;
       num_to_send = 1;
   {% endif %}

   {% if challenge.give_task_exception_port %}
       send_inline_port_message_t send_msg = {};
       send_msg.header.msgh_bits = MACH_MSGH_BITS_SET(
          /* remote */ MACH_MSG_TYPE_COPY_SEND,
          /* local */ 0,
          /* voucher */ 0,
          /* other */ MACH_MSGH_BITS_COMPLEX);
       send_msg.header.msgh_remote_port = to_reply;
       send_msg.header.msgh_local_port = MACH_PORT_NULL;
       send_msg.header.msgh_size = sizeof(send_msg);

       send_msg.body.msgh_descriptor_count = 1;

       send_msg.port_descriptor.name = to_send[0];
       send_msg.port_descriptor.disposition = MACH_MSG_TYPE_MOVE_RECEIVE;
       send_msg.port_descriptor.type = MACH_MSG_PORT_DESCRIPTOR;


   {% else %}
       send_port_message_t send_msg = {};
       send_msg.header.msgh_bits = MACH_MSGH_BITS_SET(
          /* remote */ MACH_MSG_TYPE_COPY_SEND,
          /* local */ 0,
          /* voucher */ 0,
          /* other */ MACH_MSGH_BITS_COMPLEX);
       send_msg.header.msgh_remote_port = to_reply;
       send_msg.header.msgh_local_port = MACH_PORT_NULL;

       send_msg.descriptor_count = 1;

       send_msg.descriptor.address = &to_send;
       send_msg.descriptor.count = num_to_send;
       send_msg.descriptor.copy = MACH_MSG_PHYSICAL_COPY;
       send_msg.descriptor.deallocate = false;
       send_msg.descriptor.type = MACH_MSG_OOL_PORTS_DESCRIPTOR;
       send_msg.descriptor.disposition = MACH_MSG_TYPE_COPY_SEND;
   {% endif %}

    // Send the message.
    kr = mach_msg(
        &send_msg.header,  // Same as (mach_msg_header_t *) &message.
        MACH_SEND_MSG,    // Options. We're sending a message.
        sizeof(send_msg),  // Size of the message being sent.
        0,                // Size of the buffer for receiving.
        MACH_PORT_NULL,   // A port to receive a message on, if receiving.
        MACH_MSG_TIMEOUT_NONE,
        MACH_PORT_NULL    // Port for the kernel to send notifications about this message to.
    );
    if (kr != KERN_SUCCESS) {
        printf("mach_msg() failed with code 0x%x\n", kr);
        return 1;
    }

    // busy loop
    while (1)
    {
       {% if challenge.leak_win_variable %}
       if (win == 0x31337)
       {
          printf("Here's your flag: %s\n", flag);
       }
       {% elif challenge.give_task_exception_port %}
           char c = getchar();
           sleep(1);
           c = *(char*)c;
       {% else %}
           sleep(1);
       {% endif %}
    }


}
{% endblock %}



