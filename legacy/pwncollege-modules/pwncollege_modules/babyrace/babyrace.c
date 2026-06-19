{% extends "base/base.c" %}

{% set walkthrough_pause %}
  {% if walkthrough %}
    puts("Paused (press enter to continue)");
    getchar();
  {% endif %}
{% endset %}

{% block main %}
  struct stat stat_data;
  {% if challenge.read or challenge.sendfile %}
    {% if challenge.win_variable %}
      struct {
        char read_buffer[{{ challenge.read_buffer_size }}];
        unsigned long long win_variable;
      } data;
      data.win_variable = 0;
      {% set read_buffer = "data.read_buffer" %}
    {% else %}
      char read_buffer[{{ challenge.read_buffer_size }}];
      {% set read_buffer = "read_buffer" %}
    {% endif %}
  {% endif %}

  {% filter layout_text_walkthrough %}
    Through this series of challenges, you will become familiar with the concept of race conditions.
    This challenge allows you to open a single file, as specified by the first argument to the program (argv[1]).
  {% endfilter %}

  {% if challenge.sendfile %}
    {{ "The file opened will be be sent to you." | layout_text_walkthrough }}
  {% elif challenge.read %}
    {{ "The file opened will be read in." | layout_text_walkthrough }}
  {% endif %}

  {% if walkthrough %}
    puts("This challenge will verify that the file's path does not include \"flag\".");
    puts("This challenge will verify that the file is not a symlink.");
    {% if challenge.max_size %}
      puts("This challenge will verify that the file is not larger than {{ challenge.max_size }} bytes.");
    {% endif %}
    {% if challenge.check_directory_stat or challenge.check_directory_lstat %}
      puts("This challenge will verify that the directory the file is in is owned by root");
      puts("and that other users are not able to create files in that directory.");
    {% endif %}
  {% endif %}

  assert(argc > 1);

  if (strstr(argv[1], "flag")) {
    puts("Error: path contains `flag`!");
    exit(1);
  }

  {{ "Calling lstat (does not follow symlinks) on the path." | layout_text_walkthrough }}

  {{ walkthrough_pause }}

  if (lstat(argv[1], &stat_data) == -1) {
    puts("Error: failed to get file status!");
    exit(1);
  }

  if (S_ISLNK(stat_data.st_mode)) {
    puts("Error: file is a symlink!");
    exit(1);
  }

  {% if challenge.max_size %}
    if (stat_data.st_size > {{ challenge.max_size }}) {
      puts("Error: file is too large!");
      exit(1);
    }
  {% endif %}

  {% if challenge.check_directory_stat or challenge.check_directory_lstat %}
    {% if challenge.check_directory_stat %}
      {{ "Calling stat (follows symlinks) on the directory." | layout_text_walkthrough }}
      {% set stat_func = "stat" %}
    {% elif challenge.check_directory_lstat %}
      {{ "Calling lstat (does not follow symlinks) on the directory." | layout_text_walkthrough }}
      {% set stat_func = "lstat" %}
    {% endif %}

    {{ walkthrough_pause }}

    if ({{ stat_func }}(dirname(strdup(argv[1])), &stat_data) == -1) {
      puts("Error: failed to get directory status!");
      exit(1);
    }

    if (stat_data.st_uid != 0) {
      puts("Error: directory not owned by root!");
      exit(1);
    }

    if (stat_data.st_gid != 0) {
      puts("Error: directory not group owned by root!");
      exit(1);
    }

    if (stat_data.st_mode & S_IWOTH) {
      puts("Error: other users are able to write in this directory!");
      exit(1);
    }
  {% endif %}

  {% if challenge.sleep %}
    {{ "Sleeping for {}us!".format(challenge.sleep) | layout_text_walkthrough }}
    usleep({{ challenge.sleep }});
  {% endif %}

  {{ walkthrough_pause }}

  {% if challenge.sendfile %}
    write(1, {{ read_buffer }}, read(open(argv[1], 0), {{ read_buffer }}, {{ challenge.read_buffer_size }}));

  {% elif challenge.read %}
    read(open(argv[1], 0), {{ read_buffer }}, {{ challenge.read_size }});
    {% if challenge.win_variable %}
      {% if walkthrough %}
        printf("Value of \"win\" variable: %llx\n", data.win_variable);
      {% endif %}
      if (data.win_variable)
        win();
    {% endif %}
  {% endif %}
{% endblock %}
