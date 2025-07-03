


class DataModel:
    def to_dict(
        self, 
        *, 
        exclude_none: bool = False,
        
    ) -> dict:
        """ Convert dataclass to dict

        Notes:
            * Can only be used with @dataclass
            * A TypeError will be raised if self contains a field that cannot be deep copied (e.g. sys.stdout).
        
        :param bool exclude_none: _description_, defaults to False
        :raises TypeError: _description_
        :return dict: _description_
        """
        from dataclasses import asdict, is_dataclass
        
        if not is_dataclass(self):
            raise TypeError("to_dict() should be called on dataclass instances")
        
        if exclude_none:
            return {k: v for k, v in asdict(self).items() if v is not None}
        
        return asdict(self)
