{% extends "mac_base/mac_base.c" %}

{% block includes %}

  typedef struct {
     mach_msg_header_t header;
     uint64 body_message;
     mach_msg_trailer_t trailer;
  } message_t;

  typedef struct {
     mach_msg_header_t header;
     char flag[256];
  } flag_inline_message_t;

  typedef struct {
     mach_msg_header_t header;
     unsigned int body_size;
     char body[512];
     mach_msg_trailer_t trailer;
  } overflow_message_t;


  typedef struct {
     mach_msg_header_t header;
     mach_msg_size_t descriptor_count;
     mach_msg_ool_descriptor_t descriptor;
  } flag_ool_message_t;


  typedef struct {
     mach_msg_header_t header;
     mach_msg_size_t descriptor_count;
     mach_msg_descriptor_t descriptor;
     mach_msg_trailer_t trailer;
  } complex_message_t;


   void debug_msg(message_t* msg)
   {
      {% if walkthrough %}
      printf("msg.msgh_bits = 0x%x\n", msg->header.msgh_bits);
      printf("msg.msgh_size = 0x%x\n", msg->header.msgh_size);
      if (MACH_MSGH_BITS_HAS_REMOTE(msg->header.msgh_bits))
      {
         printf("msg.msgh_remote_port = 0x%x\n", msg->header.msgh_remote_port);
      }
      if (MACH_MSGH_BITS_HAS_LOCAL(msg->header.msgh_bits))
      {
         printf("msg.msgh_local_port = 0x%x\n", msg->header.msgh_local_port);
      }
      printf("msg.msgh_id = 0x%x\n", msg->header.msgh_id);
      if (MACH_MSGH_BITS_IS_COMPLEX(msg->header.msgh_bits))
      {
         // ...
      }
      else
      {
         printf("body_message = 0x%llx\n", msg->body_message);
      }
      {% endif %}
   }

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

static void send_flag_inline_to_port(mach_port_t port)
{
   kern_return_t kr;
   flag_inline_message_t msg = {};
   msg.header.msgh_bits = MACH_MSGH_BITS_SET(
      /* remote */ MACH_MSG_TYPE_COPY_SEND,
      /* local */ 0,
      /* voucher */ 0,
      0);
   msg.header.msgh_remote_port = port;
   msg.header.msgh_local_port = MACH_PORT_NULL;

   get_flag(&msg.flag, sizeof(msg.flag));

   kr = mach_msg(
      &msg.header,  // Same as (mach_msg_header_t *) &message.
      MACH_SEND_MSG,    // Options. We're sending a message.
      sizeof(msg),  // Size of the message being sent.
      0,                // Size of the buffer for receiving.
      MACH_PORT_NULL,   // A port to receive a message on, if receiving.
      MACH_MSG_TIMEOUT_NONE,
      MACH_PORT_NULL    // Port for the kernel to send notifications about this message to.
      );
   if (kr != KERN_SUCCESS) {
      {% if walkthrough %}
          printf("mach_msg() failed with code 0x%x\n", kr);
      {% endif %}
      exit(-1);
   }
}

static void send_flag_ool_to_port(mach_port_t port)
{
   kern_return_t kr;
   flag_ool_message_t msg = {};
   msg.header.msgh_bits = MACH_MSGH_BITS_SET(
      /* remote */ MACH_MSG_TYPE_COPY_SEND,
      /* local */ 0,
      /* voucher */ 0,
      /* other */ MACH_MSGH_BITS_COMPLEX);
   msg.header.msgh_remote_port = port;
   msg.header.msgh_local_port = MACH_PORT_NULL;


   char* flag = calloc(1, 256);
   get_flag(flag, 256);

   msg.descriptor_count = 1;
   msg.descriptor.address = flag;
   msg.descriptor.size = 256;
   msg.descriptor.copy = MACH_MSG_VIRTUAL_COPY;
   msg.descriptor.deallocate = false;
   msg.descriptor.type = MACH_MSG_OOL_DESCRIPTOR;

   kr = mach_msg(
      &msg.header,  // Same as (mach_msg_header_t *) &message.
      MACH_SEND_MSG,    // Options. We're sending a message.
      sizeof(msg),  // Size of the message being sent.
      0,                // Size of the buffer for receiving.
      MACH_PORT_NULL,   // A port to receive a message on, if receiving.
      MACH_MSG_TIMEOUT_NONE,
      MACH_PORT_NULL    // Port for the kernel to send notifications about this message to.
      );
   if (kr != KERN_SUCCESS) {
      {% if walkthrough %}
          printf("mach_msg() failed with code 0x%x\n", kr);
      {% endif %}
      exit(-1);
   }
}
{% endif %}

{% if challenge.stack_overflow_on_message %}
static char* overflow_me(char* to_read, uint64 read_size)
{
   char buf[0x20];
   char* to_return = to_read;
   (memcpy)(buf, to_read, read_size);
   return to_return;
}
{% endif %}

{% endblock %}

{% block globals %}

  {% if challenge.force_import %}
    void force_import()
    {
      {% for import in challenge.force_import %}
        ((void(*)()){{ import }})();
      {% endfor %}
    }
  {% endif %}

  {% if challenge.free_gadgets %}
    void free_gadgets()
    {
      {% for gadget in challenge.free_gadgets %}
        long long variable_{{ loop.index0 }} = 0x{{ gadget[::-1].hex() }};
      {% endfor %}
    }
  {% endif %}

  {% if challenge.free_gadgets_asm %}
    void free_gadgets_asm()
    {
      {% for asm in challenge.free_gadgets_asm %}
      asm volatile ("{{ asm | replace(';', '\\n') }}" :  : : );
      {% endfor %}
    }
  {% endif %} 

{% endblock %}

{% block main %}
  char crash_resistance[0x1000];  
{% endblock %}

{% block challenge_function %}
    {% if challenge.leak_challenge %}
        printf("[LEAK] The address of challenge is: %p\n\n", &challenge);
    {% endif %}

    {% if challenge.listen_for_message %}
        mach_port_t receive_port;
        kern_return_t kr = mach_port_allocate(mach_task_self(), MACH_PORT_RIGHT_RECEIVE, &receive_port);
        if (kr != KERN_SUCCESS) {
            printf("mach_port_allocate() failed with code 0x%x\n", kr);
            return 1;
        } 
        {% if walkthrough %}
            printf("mach_port_allocate() created port right name %d\n", receive_port);
        {% endif %}

        kr = mach_port_insert_right(mach_task_self(), receive_port, receive_port, MACH_MSG_TYPE_MAKE_SEND);
        if (kr != KERN_SUCCESS) {
            printf("mach_port_insert_right() failed with code 0x%x\n", kr);
            return 1;
        }
        {% if walkthrough %}
            printf("mach_port_insert_right() inserted a send right\n");
        {% endif %}

        kr = bootstrap_register(bootstrap_port, "{{ challenge.our_register_port_name }}", receive_port);
        if (kr != KERN_SUCCESS) {
            printf("bootstrap_register() failed with code 0x%x\n", kr);
            return 1;
        }
        {% if walkthrough %}
            printf("bootstrap_register() to {{ challenge.our_register_port_name }}\n");
        {% endif %}

        {% if challenge.stack_overflow_on_message and not challenge.require_complex_message %}
            {% set msg_type = "overflow_message_t" %}
        {% elif challenge.require_complex_message %}
          {% set msg_type = "complex_message_t" %}
        {% else %}
            {% set msg_type = "message_t" %}
        {% endif %}

        {{ msg_type }} msg = {};

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

        if (MACH_MSGH_BITS_IS_COMPLEX(msg.header.msgh_bits))
        {     
           {% if not challenge.require_complex_message %}
               {% if walkthrough %}
                   printf("Error: got complex message but expected simple");
               {% endif %}
               exit(-1);
           {% endif %}
        }
        else
        {
           {% if challenge.require_complex_message %}
               {% if walkthrough %}
                   printf("Error: got simple message but expected complex");
               {% endif %}
           exit(-1);
           {% endif %}
        }


        {% if challenge.required_inline_message_value %}
            if (msg.body_message != {{ challenge.required_inline_message_value }}uLL)
            {
               {% if walkthrough %}
                   printf("Error: expected 0x%llx in message body, got 0x%llx", {{ challenge.required_inline_message_value }}uLL, msg.body_message);
               {% endif %}
               exit(-1); 
            }
        {% endif %}

        {% if challenge.require_descriptor_type %}
            
            if (msg.descriptor_count != 1)
            {
               {% if walkthrough %}
                   printf("Error: expected 1 descriptor in message body, got 0x%llx", msg.descriptor_count);
               {% endif %}
               exit(-1); 
            }

            if (msg.descriptor.type.type != {{ challenge.require_descriptor_type }})
            {
               {% if walkthrough %}
                   printf("Error: expected 0x%x as descriptor type, instead got 0x%x", {{ challenge.require_descriptor_type }}, msg.descriptor.type);
               {% endif %}
               exit(-1); 
            }
        {% endif %}

        {% if challenge.required_ool_message_value %}
            mach_msg_ool_descriptor_t* ool_descriptor = &msg.descriptor;
            if (ool_descriptor->size != sizeof(uint64))
            {
                 {% if walkthrough %}
                     printf("Error: incorrect size sent for OOL message");
                 {% endif %}
                 exit(-1); 
            }
            uint64 value = *(uint64*)ool_descriptor->address;
            if (value != {{ challenge.required_ool_message_value }}uLL)
            {
                 {% if walkthrough %}
                 printf("Error: OOL message has value 0x%llx, expected 0x%llx", value, {{ challenge.required_ool_message_value}}uLL);
                 {% endif %}
                 exit(-1); 
            }
        {% endif %}

        {% if challenge.call_win_on_message %}
            win();
        {% endif %}

        {% if challenge.stack_overflow_on_message %}
            {% if challenge.require_complex_message %}
                mach_msg_ool_descriptor_t* ool_descriptor = &msg.descriptor;
                {% if challenge.gadgets_after_overflow_return %}
                    overflow_me(ool_descriptor->address, (unsigned char)(*(unsigned char *)ool_descriptor->address));
                    if (msg.descriptor.type.type != {{ challenge.require_descriptor_type }}) {
                        asm volatile ("{{ challenge.gadgets_after_overflow_return | replace(';', '\\n') }}" :  : : );
                    }
                {% else %}
                    overflow_me(ool_descriptor->address, ool_descriptor->size);
                {% endif %}

            {% else %}
                overflow_me(msg.body, msg.body_size);
            {% endif %}
        {% endif %}
        

        {% if challenge.send_flag_inline_message %}
            send_flag_inline_to_port(msg.header.msgh_remote_port);
        {% endif %}

        {% if challenge.send_flag_ool_message %}
            send_flag_ool_to_port(msg.header.msgh_remote_port);
        {% endif %}

    {% endif %}

    {% if challenge.send_a_message %}
        mach_port_t port;
        {% if walkthrough %}
            printf("attempt to boostrap_look_up() to {{ challenge.challenge_register_port_name }}\n");
        {% endif %}

        kern_return_t kr = bootstrap_look_up(bootstrap_port, "{{ challenge.challenge_register_port_name }}", &port);
        if (kr != KERN_SUCCESS) {
           {% if walkthrough %}
               printf("bootstrap_look_up() failed with code 0x%x\n", kr);
           {% endif %}
           return 1;
        }

        {% if challenge.send_flag_inline_message %}
            send_flag_inline_to_port(port);
        {% endif %}

        {% if challenge.send_flag_ool_message %}
            send_flag_ool_to_port(port);
        {% endif %}
    {% endif %}

    return 0;
  
{% endblock %}
