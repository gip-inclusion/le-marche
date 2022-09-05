class StatsRouter:
    """
    A router to control all database operations on models in the
    stat application.
    """

    route_app_labels = {"stats"}

    db_stats = "stats"

    def db_for_read(self, model, **hints):
        """
        Attempts to read Tracker models go to stats db.
        """
        if model._meta.app_label in self.route_app_labels:
            return self.db_stats
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write Tracker models go to stats db.
        """
        if model._meta.app_label in self.route_app_labels:
            return self.db_stats
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the  Tracker models go to stats db.
        """
        if obj1._meta.app_label in self.route_app_labels or obj2._meta.app_label in self.route_app_labels:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure Tracker models go to stats db.
        """
        if app_label in self.route_app_labels:
            return db == self.db_stats
        return None
