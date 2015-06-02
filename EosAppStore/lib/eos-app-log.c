/* Copyright 2015 Endless Mobile, Inc. */
#include "eos-app-log.h"

#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <systemd/sd-journal.h>

static void
eos_app_log_messagev (int level,
                      const char *fmt,
                      va_list args)
{
  static char eos_app_testing = '\0';
  static char eos_app_journal_debugging = '\0';

  if (eos_app_testing == '\0') {
    const char *env = g_getenv ("EAS_TESTING");
    if (env != NULL && *env == '1')
      eos_app_testing = '1';
    else
      eos_app_testing = '0';
  }

  if (eos_app_journal_debugging == '\0') {
    const char *env = g_getenv ("EAS_DEBUG_JOURNAL");
    if (env != NULL && *env == '1')
      eos_app_journal_debugging = '1';
    else
      eos_app_journal_debugging = '0';
  }

  if (eos_app_journal_debugging == '1') {
    sd_journal_printv (level, fmt, args);
    return;
  }

  switch (level) {
    case LOG_DEBUG:
      g_logv (G_LOG_DOMAIN, G_LOG_LEVEL_DEBUG, fmt, args);
      return;

    case LOG_INFO:
      g_logv (G_LOG_DOMAIN, G_LOG_LEVEL_INFO, fmt, args);
      return;

    case LOG_ERR:
      /* if we're not under a test environment, then we send
       * errors to the journal
       */
      if (eos_app_testing == '0') {
        sd_journal_printv (level, fmt, args);
      } else {
        vfprintf (stderr, fmt, args);
        fputc ('\n', stderr);
      }
      return;

    default:
      break;
  }
}

void
eos_app_log_debug_message (const char *fmt,
                           ...)
{
  va_list args;

  va_start (args, fmt);

  eos_app_log_messagev (LOG_DEBUG, fmt, args);

  va_end (args);
}

void
eos_app_log_error_message (const char *fmt,
                           ...)
{
  va_list args;

  va_start (args, fmt);

  eos_app_log_messagev (LOG_ERR, fmt, args);

  va_end (args);
}

void
eos_app_log_info_message (const char *fmt,
                          ...)
{
  va_list args;

  va_start (args, fmt);

  eos_app_log_messagev (LOG_INFO, fmt, args);

  va_end (args);
}
