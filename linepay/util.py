# -*- coding: utf-8 -*-

import inspect
import logging

LOGGER = logging.getLogger('linepay')


def validate_function_args_return_value(func):
    """decorator for function arguments and return value
    :param func:
    :return:
    """
    def validate_function_args_return_value_wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        # 引数の検証
        for args_name, bound_args in bound_args.arguments.items():
            args_type = sig.parameters[args_name].annotation
            # 型が指定されている(not empty)、かつ 型が一致していない場合エラー
            actual_type = type(bound_args)
            if args_type is not inspect._empty and actual_type != args_type:
                msg = 'Argument[{arg_name}] type is invalid. Expect {expect_type} but passed {actual_type}'.format(
                    arg_name=args_name,
                    expect_type=args_type,
                    actual_type=actual_type
                )
                raise ValueError(msg)
        # 関数の実行
        results = func(*args, **kwargs)

        # 返り値の検証
        return_type = sig.return_annotation
        # 型が指定されている(not empty)、かつ型が一致していない場合エラー
        if return_type is not inspect._empty and type(results) != return_type:
            raise ValueError(
                'retrun value is not valid type. expected[{expect_type}] but was [{actual_type}]'.format(
                    expect_type=return_type,
                    actual_type=type(results)
                )
            )
        return results
    return validate_function_args_return_value_wrapper
